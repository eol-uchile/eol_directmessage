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
    enrolled_students = get_all_students(course_key)
    return {
        "course" : course,
        "students" : enrolled_students,
        "user_id" : request.user.id,
        "username" : request.user.profile.name,
        "url_get_chats" : reverse('get_chats', kwargs={
            'course_id' : course_id
        }),
    }

def get_all_students(course_key):
    return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
    )

def get_chats(request, course_id):
    """
        get_chats return json with the user chats.
        max_viewed will be 'False' if the user has new messages
    """
    user_id = request.user.id
    user_chats = EolMessage.objects.filter(
        Q(sender_user=user_id) | Q(receiver_user=user_id),
        course_id = course_id,
        deleted_at__isnull=True
    ).values('sender_user__profile__name', 'receiver_user__profile__name').annotate(min_viewed = Min('viewed'), max_date = Max('created_at')).order_by('-max_date')
    user_chats = list(user_chats)
    #data = serializers.serialize('json', user_chats)
    #struct = json.loads(data)
    data = json.dumps(user_chats, default=json_util.default)
    return HttpResponse(data)

