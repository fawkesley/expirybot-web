import logging

from .mixins import GetLoginContextMixin
from . import LoginGetEmailAddressView

LOG = logging.getLogger(__name__)


class LoginWithContextView(GetLoginContextMixin, LoginGetEmailAddressView):
    pass
