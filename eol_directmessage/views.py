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
from models import EolMessage

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
        })
    }


def get_all_students(user_id, course_key):
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
    sender_chats = EolMessage.objects.filter(
        Q(sender_user=user_id),
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
    )

    receiver_chats = EolMessage.objects.filter(
        Q(receiver_user=user_id),
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
    )

    # Merge two QuerySet and order by date
    user_chats = (sender_chats | receiver_chats).order_by('-max_date')
    user_chats = list(user_chats)

    # delete duplicated
    users_already = [] # list of other students usernames
    for u in user_chats:
        other_user = u["sender_user__username"] if u["sender_user__username"] != request.user.username else u["receiver_user__username"] # get student username
        if other_user in users_already:
            user_chats.remove(u) # remove object if already exists on the list
        else:
            users_already.append(other_user)

    data = json.dumps(user_chats, default=json_util.default)
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
    messages = list(messages)
    data = json.dumps(messages, default=json_util.default)
    return HttpResponse(data)