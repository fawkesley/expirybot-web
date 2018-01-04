import logging

from django.contrib.auth.views import (
    LogoutView as AuthLogoutView,
)

LOG = logging.getLogger(__name__)


class LogoutView(AuthLogoutView):
    template_name = 'users/logout.html'
