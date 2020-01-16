from __future__ import absolute_import

from django.conf.urls import url
from django.conf import settings

from .views import EolDirectMessageFragmentView


urlpatterns = (
    url(
        r'courses/{}/direct_message$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        EolDirectMessageFragmentView.as_view(),
        name='directmessage_view',
    ),
)
