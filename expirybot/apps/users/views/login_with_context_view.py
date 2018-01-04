import logging

from .mixins import GetLoginContextMixin
from . import LoginView

LOG = logging.getLogger(__name__)


class LoginWithContextView(GetLoginContextMixin, LoginView):
    pass
