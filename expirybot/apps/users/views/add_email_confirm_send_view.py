import datetime
import logging

import jwt

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, reverse
from django.utils import timezone
from django.views.generic import TemplateView

from ..email_helpers import send_validation_email

from .mixins import EmailAddressContextFromURLMixin

LOG = logging.getLogger(__name__)


class AddEmailConfirmSendView(LoginRequiredMixin,
                              EmailAddressContextFromURLMixin,
                              TemplateView):
    template_name = 'users/add_email_confirm_send.html'

    def post(self, request, *args, **kwargs):
        self._send_validation_email(self.get_email_address())

        return redirect(
            reverse(
                'users.email-sent',
                kwargs={
                    'b64_email_address': self.kwargs['b64_email_address']
                }
            )
        )

    def get_login_url(self):
        return reverse(
            'users.sign-up-with-context', kwargs={'login_context': 'add-email'}
        )

    def _send_validation_email(self, email_address):
        jwt_data = {
            'exp': timezone.now() + datetime.timedelta(days=7),
            'a': 'add-email',
            'e': email_address,
            'u': str(self.request.user.profile.uuid),
        }

        validation_url = self.request.build_absolute_uri(
            reverse(
                'users.add-email-address',
                kwargs={
                    'json_web_token': jwt.encode(jwt_data, settings.SECRET_KEY)
                }
            )
        )

        send_validation_email(email_address, validation_url)
