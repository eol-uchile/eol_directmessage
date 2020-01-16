from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab
import django_comment_client.utils as utils
from xmodule.tabs import TabFragmentViewMixin

from django.contrib.auth.models import User


class EolDirectMessageTab(TabFragmentViewMixin, EnrolledTab):
    type = 'eol_directmessage'
    title = ugettext_noop('Messages')
    priority = None
    view_name = 'directmessage_view'
    fragment_view_name = 'eol_directmessage.views.EolDirectMessageFragmentView'
    is_hideable = True
    is_default = True
    body_class = 'eol_directmessage'
    online_help_token = 'eol_directmessage'

    @classmethod
    def is_enabled(cls, course, user=None):
        """
            Check if user is enrolled on course
        """
        if not super(EolDirectMessageTab, cls).is_enabled(course, user):
            return False
        return configuration_helpers.get_value(
            'EOL_DIRECTMESSAGE_TAB_ENABLED', False)
