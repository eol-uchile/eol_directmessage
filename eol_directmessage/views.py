# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from courseware.courses import get_course_with_access
from courseware.access import has_access
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User

from django.urls import reverse
from django.http import HttpResponse, Http404
from bson import json_util
import json
from django.core import serializers

from django.db.models import Q, Min, Max
from models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration, EolMessageFilter
from student.models import CourseAccessRole

import logging
logger = logging.getLogger(__name__)

# Default username used to create url_get_message. It will be replaced in
# the javascript
DEFAULT_USERNAME = 'DEFAULT_USERNAME_EOLDIRECTMESSAGE'
DEFAULT_ONLY_STAFF = False


class EolDirectMessageFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        if(not self.has_page_access(request.user, course_id)):
            raise Http404()
        context = _get_context(request, course_id)
        html = render_to_string(
            'eol_directmessage/eol_directmessage_fragment.html', context)
        fragment = Fragment(html)
        return fragment

    def has_page_access(self, user, course_id):
        course_key = CourseKey.from_string(course_id)
        return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            pk=user.id
        ).exists()


def _get_context(request, course_id):
    """
        Get all attributes required
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    enrolled_students = _get_all_students(request.user.id, course_id)
    user_configuration = _get_user_configuration(request.user, course_key)
    only_staff_filter = _get_only_staff_filter(request.user, course)
    return {
        "course": course,
        "students": enrolled_students,
        "user": request.user,
        "username": request.user.profile.name,
        "user_config": user_configuration,
        "only_staff_filter": only_staff_filter,
        "url_get_student_chats": reverse(
            'get_student_chats',
            kwargs={
                'course_id': course_id}),
        "default_username": DEFAULT_USERNAME,
        "url_get_messages": reverse(
            'get_messages',
            kwargs={
                'username': DEFAULT_USERNAME,
                'course_id': course_id}),
        "url_new_message": reverse('new_message'),
        "url_update_configuration": reverse(
            'update_user_configuration',
            kwargs={
                'course_id': course_id}),
    }


def _get_only_staff_filter(user, course):
    """
        Reason: Some courses / Sites wants a chat between student-staff (without chats student-student)
        Return only_staff filter
        If user is staff or instructor, default is TRUE
        Get value from EolMessage model (by Course) or Settings (by Site)
    """
    if(bool(has_access(user, 'staff', course)) or bool(has_access(user, 'instructor', course))):
        return False
    try:
        course_filter = EolMessageFilter.objects.get(course_id=course.id)
        return course_filter.only_staff
    except EolMessageFilter.DoesNotExist:
        return configuration_helpers.get_value(
            'EOL_DIRECTMESSAGE_ONLY_STAFF', DEFAULT_ONLY_STAFF)


def _get_all_students(user_id, course_id):
    """
        Get all student enrolled in the course (except user logged)
    """
    course_key = CourseKey.from_string(course_id)
    roles = get_access_roles(course_id)
    users = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1
    ).exclude(id=user_id)
    for u in users:
        u.has_role = u.username in roles
    return users


def _get_user_configuration(user, course_key):
    """
        Get user configuration
        For the moment only have is_muted attribute
    """
    try:
        user_config = EolMessageUserConfiguration.objects.get(
            user_id=user.id, course_id=course_key)
        return {
            "is_muted": user_config.is_muted,
        }
    except EolMessageUserConfiguration.DoesNotExist:
        return {
            "is_muted": False,
        }


def get_student_chats(request, course_id):
    """
        get_student_chats return json with the user chats (usernames).
        max_viewed will be 'False' if the user has new messages
    """
    user_id = request.user.id

    # getting user messages as sender or receiver
    user_chats = EolMessage.objects.filter(
        Q(sender_user=user_id) | Q(receiver_user=user_id),
        course_id=course_id,
        deleted_at__isnull=True
    ).values(
        'sender_user__profile__name',
        'receiver_user__profile__name',
        'sender_user__username',
        'receiver_user__username'
    ).annotate(
        min_viewed=Min('viewed'),
        max_date=Max('created_at')
    ).order_by('-max_date')

    user_chats = list(user_chats)

    # "delete" duplicated
    users_already = []  # list of other students usernames
    new_user_chats = []
    roles = get_access_roles(course_id)
    for u in user_chats:
        # get student username
        other_user = u["sender_user__username"] if u["sender_user__username"] != request.user.username else u["receiver_user__username"]
        if other_user not in users_already:
            users_already.append(other_user)
            u["has_role"] = other_user in roles
            new_user_chats.append(u)

    data = json.dumps(new_user_chats, default=json_util.default)
    return HttpResponse(data)


def get_access_roles(course_id):
    """
        Return users lists with access roles (staff and instructor)
    """
    course_key = CourseKey.from_string(course_id)
    roles = CourseAccessRole.objects.filter(
        role__in=('staff', 'instructor'),
        course_id=course_key
    ).values_list(
        'user__username',
        flat=True,
    )
    return list(roles)


def get_messages(request, username, course_id):
    """
        get_messages return json with the messages between two users
        'username' is from another student
    """
    user_id = request.user.id
    messages = EolMessage.objects.filter(
        Q(sender_user=user_id) | Q(receiver_user=user_id),
        Q(sender_user__username=username) | Q(receiver_user__username=username),
        course_id=course_id,
        deleted_at__isnull=True
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
        viewed=False
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
        sender_user=user,
        receiver_user=other_user,
        text=message.strip()
    )
    return HttpResponse(status=201)


def update_user_configuration(request, course_id):
    """
       Update user notifications configuration
    """
    # check method
    if request.method != "POST":
        return HttpResponse(status=400)

    user = request.user
    # change is_muted attribute. Create if doesn't exist
    try:
        user_config = EolMessageUserConfiguration.objects.get(
            user_id=user.id, course_id=course_id)
        user_config.is_muted = not user_config.is_muted
        user_config.save()
        return HttpResponse(status=200)
    except EolMessageUserConfiguration.DoesNotExist:
        user_config = EolMessageUserConfiguration.objects.create(
            user_id=user.id,
            course_id=course_id
        )
    return HttpResponse(status=201)
