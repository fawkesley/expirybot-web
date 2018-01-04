import logging

from .mixins import GetLoginContextMixin

from . import SignUpView

LOG = logging.getLogger(__name__)


class SignUpWithContextView(GetLoginContextMixin, SignUpView):
    pass
