import logging
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
)


LOG = logging.getLogger(__name__)


class LoginView(AuthLoginView):
    template_name = 'users/login.html'
