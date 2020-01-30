
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings

from celery import current_task, task
from django.core.mail import send_mail
from django.utils.html import strip_tags

import logging
logger = logging.getLogger(__name__)

@task(queue='edx.lms.core.low',default_retry_delay=settings.BULK_EMAIL_DEFAULT_RETRY_DELAY, max_retries=settings.BULK_EMAIL_MAX_RETRIES)
def send_reminder_mail(subject, html_message, user_email):
    """
        Send mail to specific user
    """
    plain_message = strip_tags(html_message)
    from_email = configuration_helpers.get_value(
        'email_from_address',
        settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
    )
    mail = send_mail(
        subject, 
        plain_message,
        from_email, 
        [user_email], 
        fail_silently=False,
        html_message=html_message)