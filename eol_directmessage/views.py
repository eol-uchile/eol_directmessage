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
        "url_get_chats" : reverse('get_chats', kwargs={
            'user_id' : request.user.id,
            'course_id' : course_id
        }),
    }

def get_all_students(course_key):
    return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
    )

def get_chats(request, user_id, course_id):
    logger.warning("OK")
    return HttpResponse()

