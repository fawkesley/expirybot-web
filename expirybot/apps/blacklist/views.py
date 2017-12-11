import jwt

from django.conf import settings
from django.views.generic import TemplateView

from .models import BlacklistedEmailAddress


class GetEmailAddressFromJwtMixin:

    def get_email_address(self):
        json_web_token = self.kwargs['json_web_token']

        try:
            result = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.exceptions.ExpiredSignatureError:
            # TODO: handle this
            raise

        except jwt.exceptions.InvalidTokenError:
            # TODO: handle more general types of token error
            # https://github.com/jpadilla/pyjwt/blob/master/jwt/exceptions.py
            raise

        return result['email_address']


class UnsubscribeEmailView(GetEmailAddressFromJwtMixin, TemplateView):
    """
    Accessing this view creates a BlacklistedEmailAddress
    """

    template_name = 'blacklist/unsubscribe_email.html'

    def get_context_data(self, *args, **kwargs):
        (obj, new) = BlacklistedEmailAddress.objects.get_or_create(
            email_address=self.get_email_address()
        )

        obj.unsubscribed = True
        obj.save()

        return {
            'email_address': obj.email_address,
            'already_unsubscribed': not new,
            'unsubscribe_date': obj.created_at.date
        }
