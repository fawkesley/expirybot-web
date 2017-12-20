from django import forms
from django.forms import ValidationError

from expirybot.apps.blacklist.utils import allow_send_email


class MonitorEmailAddressForm(forms.Form):
    email_address = forms.EmailField()

    def clean_email_address(self):
        email_address = self.cleaned_data['email_address']

        if not allow_send_email(email_address):
            raise ValidationError(
                "This email address or domain is unsubscribed from all "
                "Expirybot emails."
            )

        return email_address
