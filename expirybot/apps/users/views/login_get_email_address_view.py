import datetime
import jwt

from django.conf import settings
from django.shortcuts import reverse
from django.views.generic.edit import FormView
from django.utils import timezone

from ..forms import EmailLoginForm

from ..utils import get_user_for_email_address
from ..email_helpers import send_login_email

from .mixins import GetRedirectUrlMixin


class LoginGetEmailAddressView(GetRedirectUrlMixin, FormView):
    form_class = EmailLoginForm
    template_name = 'users/login_get_email_address.html'

    def form_valid(self, form):
        email_address = form.cleaned_data['email_address']
        user = get_user_for_email_address(email_address)

        self._send_login_email(user, email_address)

        return super(LoginGetEmailAddressView, self).form_valid(form)

    def _send_login_email(self, user, email_address):
        jwt_data = {
            'exp': timezone.now() + datetime.timedelta(minutes=15),
            'a': 'login',
            'u': str(user.profile.uuid),
            'n': self.get_redirect_url(),
        }

        login_url = self.request.build_absolute_uri(
            reverse(
                'users.login-from-email-link',
                kwargs={
                    'json_web_token': jwt.encode(jwt_data, settings.SECRET_KEY)
                }
            )
        )

        send_login_email(email_address, login_url)

    def get_success_url(self):
        return reverse('users.login-email-sent')
