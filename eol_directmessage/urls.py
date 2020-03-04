from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolDirectMessageFragmentView, get_student_chats, get_messages, new_message, update_user_configuration

from django.contrib.auth.decorators import login_required


urlpatterns = (
    url(
        r'courses/{}/direct_message/chats$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(EolDirectMessageFragmentView.as_view()),
        name='directmessage_view',
    ),
    url(
        r'direct_message/get_student_chats/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_student_chats),
        name='get_student_chats',
    ),
    url(
        r'direct_message/get_messages/{}/{}/$'.format(
            settings.USERNAME_PATTERN,
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_messages),
        name='get_messages',
    ),
    url(
        r'direct_message/new_message',
        login_required(new_message),
        name='new_message',
    ),
    url(
        r'direct_message/update_configuration/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(update_user_configuration),
        name='update_user_configuration',
    ),
)
