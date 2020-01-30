# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from courseware.courses import get_course_with_access
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User

from django.urls import reverse
from django.http import HttpResponse
from bson import json_util
import json
from django.core import serializers

from django.db.models import Q, Min, Max
from models import EolMessage, EolMessageConfiguration


from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings
from celery import current_task, task
from django.core.mail import send_mail
from django.utils.html import strip_tags
import datetime
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

# Default username used to create url_get_message. It will be replaced in the javascript
DEFAULT_USERNAME = 'DEFAULT_USERNAME_EOLDIRECTMESSAGE'

class EolDirectMessageFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        context = _get_context(request, course_id)
        html = render_to_string(
            'eol_directmessage/eol_directmessage_fragment.html', context)
        fragment = Fragment(html)
        return fragment

def _get_context(request, course_id):
    """
        Get all attributes required
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    enrolled_students = get_all_students(request.user.id, course_key)
    return {
        "course" : course,
        "students" : enrolled_students,
        "user" : request.user,
        "username" : request.user.profile.name,
        "url_get_student_chats" : reverse('get_student_chats', kwargs={
            'course_id' : course_id
        }),
        "default_username" : DEFAULT_USERNAME,
        "url_get_messages" : reverse('get_messages', kwargs={
            'username' : DEFAULT_USERNAME,
            'course_id' : course_id
        }),
        "url_new_message" : reverse('new_message'),
    }


def get_all_students(user_id, course_key):
    """
        Get all student enrolled in the course (except user logged)
    """
    return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
    ).exclude(id=user_id)

def get_student_chats(request, course_id):
    """
        get_student_chats return json with the user chats.
        max_viewed will be 'False' if the user has new messages
    """
    user_id = request.user.id
    
    # getting user messages as sender or receiver
    user_chats = EolMessage.objects.filter(
        Q(sender_user=user_id) | Q(receiver_user=user_id),
        course_id = course_id,
        deleted_at__isnull=True
    ).values(
        'sender_user__profile__name', 
        'receiver_user__profile__name',
        'sender_user__username',
        'receiver_user__username'
    ).annotate(
        min_viewed = Min('viewed'),
        max_date = Max('created_at')
    ).order_by('-max_date')

    user_chats = list(user_chats)

    # "delete" duplicated
    users_already = [] # list of other students usernames
    new_user_chats = []
    for u in user_chats:
        other_user = u["sender_user__username"] if u["sender_user__username"] != request.user.username else u["receiver_user__username"] # get student username
        if other_user not in users_already:
            users_already.append(other_user)
            new_user_chats.append(u)

    data = json.dumps(new_user_chats, default=json_util.default)
    create_mail()
    return HttpResponse(data)

def get_messages(request, username, course_id):
    """
        get_messages return json with the messages between two users
        'username' is from another student
    """
    user_id = request.user.id
    messages = EolMessage.objects.filter(
        Q(sender_user=user_id) | Q(receiver_user=user_id),
        Q(sender_user__username=username) | Q(receiver_user__username=username),
        course_id = course_id,
        deleted_at__isnull = True
    ).values(
        'sender_user__profile__name', 
        'receiver_user__profile__name', 
        'receiver_user__username',
        'text', 
        'viewed', 
        'created_at'
    ).order_by('created_at')
    data = json.dumps(list(messages), default=json_util.default)

    '''
        Filter messages and set viewed = True
    '''
    not_viewed = messages.filter(
        receiver_user=user_id,
        viewed = False
    ).update(viewed=True)
    
    return HttpResponse(data)

def new_message(request):
    """
       Add new message on chat between two users
    """
    # check method and params
    if request.method != "POST":
        return HttpResponse(status=400)
    if 'message' not in request.POST or 'other_username' not in request.POST or 'course_id' not in request.POST:
        return HttpResponse(status=400)

    course_id = request.POST['course_id']
    message = request.POST['message']
    other_username = request.POST['other_username']
    other_user = User.objects.get(username=other_username)
    user = request.user

    message = EolMessage.objects.create(
        course_id=course_id,
        sender_user = user,
        receiver_user = other_user,
        text=message.strip()
    )
    return HttpResponse(status=201)

def create_mail():
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


@task(default_retry_delay=settings.BULK_EMAIL_DEFAULT_RETRY_DELAY, max_retries=settings.BULK_EMAIL_MAX_RETRIES)
def send_reminder_mail(subject, html_message, user_email):
    """
        Send mail to specific user
    """
    plain_message = strip_tags(html_message)
    from_email = configuration_helpers.get_value(
        'email_from_address',
        settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
    )
    send_mail(
        subject, 
        plain_message,
        from_email, 
        [user_email], 
        fail_silently=False,
        html_message=html_message)

