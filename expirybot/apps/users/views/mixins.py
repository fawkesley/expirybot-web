import base64
import logging


LOG = logging.getLogger(__name__)


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
