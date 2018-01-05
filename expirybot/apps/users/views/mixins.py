import base64
import logging

from django.contrib.auth.views import (
    SuccessURLAllowedHostsMixin,
)
from django.utils.http import is_safe_url


LOG = logging.getLogger(__name__)


class GetRedirectUrlMixin(SuccessURLAllowedHostsMixin):
    redirect_field_name = 'next'

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
