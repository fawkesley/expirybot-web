import base64
import datetime

import jwt

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView


from .forms import MonitorEmailAddressForm
from .email_helpers import send_validation_email


class MonitorEmailAddressView(FormView):
    template_name = 'users/monitor_email_address.html'
    form_class = MonitorEmailAddressForm

    def form_valid(self, form):
        email_address = form.cleaned_data['email_address']

        self._send_validation_email(email_address)

        b64_email_address = base64.b64encode(email_address.encode('utf-8'))

        return redirect(
            reverse(
                'users.email-sent',
                kwargs={
                    'b64_email_address': b64_email_address
                }
            )
        )

    def _send_validation_email(self, email_address):
        jwt_data = {
            'exp': timezone.now() + datetime.timedelta(minutes=30),
            'a': 'add-email',
            'e': email_address,
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


class EmailSentView(TemplateView):
    template_name = 'users/email_sent.html'

    def get_context_data(self, b64_email_address, *args, **kwargs):
        email_address = base64.b64decode(b64_email_address).decode('utf-8')

        return {
            'email_address': email_address
        }


class AddEmailAddressView(LoginRequiredMixin, FormView):
    template_name = 'users/add_email_address.html'
    form_class = MonitorEmailAddressForm


class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'
