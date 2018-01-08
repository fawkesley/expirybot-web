import jwt

from django.conf import settings
from django.views.generic import TemplateView
from django.utils import timezone

from .models import EmailAddress


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

        return result['eml']


class UnsubscribeEmailView(GetEmailAddressFromJwtMixin, TemplateView):

    template_name = 'blacklist/unsubscribe_email.html'

    def get(self, request, *args, **kwargs):
        email = self.get_email_address()
        try:
            obj = EmailAddress.objects.get(email_address=email)
        except EmailAddress.DoesNotExist:
            already_unsubscribed = False
            unsubscribe_datetime = None

        else:
            already_unsubscribed = obj.unsubscribe_datetime is not None
            unsubscribe_datetime = timezone.now()

        return self.render_to_response({
            'display_form': True,
            'email_address': email,
            'already_unsubscribed': already_unsubscribed,
            'unsubscribe_date': unsubscribe_datetime
        })

    def post(self, request, *args, **kwargs):
        (obj, new) = EmailAddress.objects.get_or_create(
            email_address=self.get_email_address()
        )

        if new:
            already_unsubscribed = False
        else:
            already_unsubscribed = obj.unsubscribe_datetime is not None

        obj.unsubscribe_datetime = timezone.now()
        obj.save()

        return self.render_to_response({
            'display_form': False,
            'email_address': obj.email_address,
            'already_unsubscribed': already_unsubscribed,
            'unsubscribe_date': obj.unsubscribe_datetime
        })
