from django import forms
from django.forms import ValidationError

from expirybot.apps.blacklist.utils import allow_send_email
from expirybot.apps.blacklist.models import EmailAddress


class MonitorEmailAddressForm(forms.Form):
    email_address = forms.EmailField()

    def clean_email_address(self):
        email_address = self.cleaned_data['email_address']

        if not allow_send_email(email_address):
            raise ValidationError(
                "This email address or domain is unsubscribed from all "
                "Expirybot emails."
            )

        elif self._already_owned(email_address):
            raise ValidationError(
                "This email address is already monitored by another account."
            )

        return email_address

    @staticmethod
    def _already_owned(email):
        try:
            email_model = EmailAddress.objects.get(email_address=email)

        except EmailAddress.DoesNotExist:
            return False

        else:
            return email_model.owner_profile is not None
