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
from .models import EmailAddressOwnershipProof, UserProfile

LOG = logging.getLogger(__name__)


class MonitorEmailAddressView(FormView):
    template_name = 'users/monitor_email_address.html'
    form_class = MonitorEmailAddressForm

    def form_valid(self, form):

        email_address = form.cleaned_data['email_address']

        b64_email_address = base64.b64encode(email_address.encode('utf-8'))

        return redirect(
            reverse(
                'users.add-email-confirm-send',
                kwargs={
                    'b64_email_address': b64_email_address
                }
            )
        )


class EmailAddressContextFromURLMixin():
    def get_context_data(self, b64_email_address, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx.update({
            'email_address': self.get_email_address()
        })
        return ctx

    def get_email_address(self):
        if self.kwargs['b64_email_address']:
            return base64.b64decode(
                self.kwargs['b64_email_address']
            ).decode('utf-8')
        else:
            return None


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
            'exp': timezone.now() + datetime.timedelta(minutes=30),
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


class EmailSentView(EmailAddressContextFromURLMixin, TemplateView):
    template_name = 'users/email_sent.html'


class AddEmailAddressView(TemplateView):
    template_name = 'users/add_email_address.html'
    form_class = MonitorEmailAddressForm

    class AddEmailError(ValueError):
        pass

    def get(self, request, *args, **kwargs):
        try:
            (email, profile) = self._validate_jwt(
                self.kwargs['json_web_token']
            )

        except self.AddEmailError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            self._add_email_address_to_profile(email, profile)
            return self.render_to_response({
                'email_address': email,
                'user': profile.user,
            })
            return super().get(request, *args, **kwargs)

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.ExpiredSignatureError:
            LOG.info("Got expired JSON web token for user {}".format(
                self.request.user.username))
            raise self.AddEmailError('The link has expired')

        except jwt.DecodeError:
            LOG.error("Got invalid JSON web token for user {}".format(
                self.request.user.username))
            raise self.AddEmailError('The link appears to be invalid')

        else:
            if data['a'] != 'add-email':
                LOG.error(
                    "Got suspicious JSON web token on add-email for "
                    "user {}: {}".format(self.request.user.username, data)
                )

                raise self.AddEmailError('The link appears to be invalid')

        email = data['e']
        try:
            profile = UserProfile.objects.get(uuid=data['u'])
        except UserProfile.DoesNotExist:
            raise self.AddEmailError(
                'The user was not found')

        return (email, profile)

    def _add_email_address_to_profile(self, email_address, profile):
        user = profile.user

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
