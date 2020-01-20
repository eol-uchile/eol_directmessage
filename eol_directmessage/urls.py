from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolDirectMessageFragmentView, get_chats

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
        r'direct_message/get_chats/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_chats),
        name='get_chats',
    ),
)
