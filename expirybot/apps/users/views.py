import base64
import datetime
import logging

import jwt

from django.conf import settings

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    LogoutView as AuthLogoutView,
    SuccessURLAllowedHostsMixin,
)

from django.shortcuts import redirect, reverse, resolve_url

from django.utils import timezone
from django.utils.http import is_safe_url

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from expirybot.apps.blacklist.models import EmailAddress

from .forms import MonitorEmailAddressForm
from .email_helpers import send_validation_email
from .models import EmailAddressOwnershipProof

LOG = logging.getLogger(__name__)


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


class AddEmailConfirmSendView(LoginRequiredMixin, TemplateView):
    template_name = 'users/add_email_confirm_send.html'

    def get_context_data(self, b64_email_address, *args, **kwargs):
        email_address = base64.b64decode(b64_email_address).decode('utf-8')

        return {
            'email_address': email_address
        }

    def get_login_url(self):
        return reverse(
            'users.sign-up-with-context', kwargs={'login_context': 'add-email'}
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


class AddEmailAddressView(LoginRequiredMixin, TemplateView):
    template_name = 'users/add_email_address.html'
    form_class = MonitorEmailAddressForm

    def get(self, request, *args, **kwargs):
        if not self._validate_jwt(self.kwargs['json_web_token']):
            return redirect(reverse('users.monitor-email-address'))

        return super(AddEmailAddressView, self).get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        email_address = self._validate_jwt(self.kwargs['json_web_token'])

        if email_address is None:
            return redirect(reverse('users.monitor-email-address'))

        self._add_email_address_to_user(email_address, self.request.user)

        return redirect(
            reverse(
                'users.settings',
            )
        )

    def get_context_data(self, *args, **kwargs):
        email_address = self._validate_jwt(self.kwargs['json_web_token'])

        return {
            'email_address': email_address
        }

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.ExpiredSignatureError:
            LOG.info("Got expired JSON web token for user {}".format(
                self.request.user.username))
            return None

        except jwt.DecodeError:
            LOG.error("Got expired JSON web token for user {}".format(
                self.request.user.username))
            return None

        else:
            if data['a'] != 'add-email':
                LOG.error(
                    "Got suspicious JSON web token on add-email for "
                    "user {}: {}".format(self.request.user.username, data)
                )

                return None

        return data['e']

    def _add_email_address_to_user(self, email_address, user):
        profile = user.profile

        (email_model, _) = EmailAddress.objects.get_or_create(
            email_address=email_address
        )

        try:
            existing_proof = EmailAddressOwnershipProof.objects.get(
                email_address=email_model
            )
        except EmailAddressOwnershipProof.DoesNotExist:
            existing_proof = None

        else:
            if existing_proof.profile != profile:
                raise RuntimeError(
                    "Prevented change of ownership of email address {} "
                    "from {} to {}".format(
                        email_address, email_model.owner_profile, profile)
                )

        if existing_proof is None:
            EmailAddressOwnershipProof.objects.create(
                profile=profile,
                email_address=email_model
            )

        if not user.email:
            # Also set user's default email address, if not set
            user.email = email_address
            user.save()


class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'


class LoginView(AuthLoginView):
    template_name = 'users/login.html'


class GetLoginContextMixin():

    def get_context_data(self, *args, **kwargs):
        """
        Translate e.g. /u/login/add-email/address to a context object with:
        {
            'login_partial': 'users/partials/login_add_user.html'
            'sign_up_partial': 'users/partials/sign_up_add_user.html'
        }
        """
        ctx = super(GetLoginContextMixin, self).get_context_data(
            *args, **kwargs
        )

        login_context = self.kwargs.get('login_context')

        if login_context:
            fn = login_context.replace('-', '_')

            ctx.update({
                'login_context': login_context,
                'login_partial': 'users/partials/login_{}.html'.format(fn),
                'sign_up_partial': 'users/partials/sign_up_{}.html'.format(fn),
            })

        return ctx


class LoginWithContextView(GetLoginContextMixin, LoginView):
    pass


class LogoutView(AuthLogoutView):
    template_name = 'users/logout.html'


class SignUpView(SuccessURLAllowedHostsMixin, FormView):
    form_class = UserCreationForm
    template_name = 'users/sign_up.html'
    redirect_field_name = 'next'

    def form_valid(self, form):
        form.save()  # save the new user first

        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']

        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(SignUpView, self).form_valid(form)

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""

        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            self.redirect_field_name: self.get_redirect_url(),
        })
        return context


class SignUpWithContextView(GetLoginContextMixin, SignUpView):
    pass
