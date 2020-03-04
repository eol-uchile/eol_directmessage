from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User
from eol_directmessage.models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration
from django.db.models import Min, Max
from courseware.courses import get_course_with_access
from django.template.loader import render_to_string

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings


import datetime
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

from eol_directmessage.tasks import send_reminder_mail

class Command(BaseCommand):
    help = 'This command will send a reminder mail to the users when they have unread messages'

    def handle(self, *args, **options):
        """
            Filter all users with unviewed messages after the last mail and generate a reminder mail
        """
        platform_name = configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
        today = timezone.now()
        
        # Get or create EolMessageConfiguration with last mail date
        configuration, created = EolMessageConfiguration.objects.get_or_create()
        users = EolMessage.objects.filter(
            viewed=False,
            created_at__range=(configuration.last_mail, today),
            deleted_at__isnull=True
        ).values(
            'receiver_user',
            'course_id'
        ).annotate(
            min_viewed = Min('viewed'),
            max_date = Max('created_at')
        )
        # Update last mail date
        configuration.last_mail = today
        configuration.save()

        # Send mail for each user
        for u in users:
            # Check if user wants to receive emails
            try:
                user_config = EolMessageUserConfiguration.objects.get(user_id=u["receiver_user"], course_id=u["course_id"])
                is_muted = user_config.is_muted
            except EolMessageUserConfiguration.DoesNotExist:
                is_muted = False
            
            if not is_muted:
                course_key = CourseKey.from_string(u["course_id"])
                user = User.objects.get(id=u["receiver_user"])
                course = get_course_with_access(user, "load", course_key)
                subject = 'Tienes nuevos mensajes en el curso "%s"' % (course.display_name_with_default)
                context = {
                    "user_full_name": user.profile.name,
                    "course_name": course.display_name_with_default,
                    "platform_name": platform_name,
                }
                html_message = render_to_string('emails/unread_direct_messages_reminder.txt', context)
                send_reminder_mail.delay(subject, html_message, user.email)