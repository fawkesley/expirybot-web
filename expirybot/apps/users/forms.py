import logging

from django import forms
from django.forms import ValidationError

from expirybot.apps.blacklist.utils import allow_send_email
from expirybot.apps.blacklist.models import EmailAddress

from .models import UserProfile
from .utils import get_user_for_email_address

LOG = logging.getLogger(__name__)


class EmailLoginForm(forms.Form):
    email_address = forms.EmailField()

    def clean_email_address(self):
        email_address = self.cleaned_data['email_address']

        if not allow_send_email(email_address):
            LOG.warning('Login attempt from blacklisted email {}'.format(
                email_address))

            raise ValidationError(
                "This email address or domain is unsubscribed from all "
                "Expirybot emails. If you think this is an error, please "
                "get in touch."
            )

        user = get_user_for_email_address(email_address)

        if not user:
            LOG.warning('Login attempt from unknown email {}'.format(
                email_address))

            raise ValidationError(
                "Could not find an account associated with that email address."
            )

        if not user.is_active:
            LOG.warning('Login attempt from inactive email {}'.format(
                email_address))
            raise ValidationError("That account is inactive.")

        return email_address


class MonitorEmailAddressForm(forms.Form):
    email_address = forms.EmailField()

    def clean_email_address(self):
        email_address = self.cleaned_data['email_address']

        if not allow_send_email(email_address):
            LOG.warning('Attempt to monitor blacklisted email {}'.format(
                email_address))

            raise ValidationError(
                "This email address or domain is unsubscribed from all "
                "Expirybot emails. If you think this is an error, please "
                "get in touch."
            )

        elif self._already_owned(email_address):
            LOG.warning('Attempt to monitor already-owned email {}'.format(
                email_address))

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


class ExtraAttrsMixin(object):
    extra_attrs = {}

    def __init__(self, *args, **kwargs):
        super(ExtraAttrsMixin, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            attrs = self.extra_attrs.get(field_name, {})

            field.widget.attrs.update(attrs)


class UserSettingsForm(ExtraAttrsMixin, forms.ModelForm):
    class Meta:
        model = UserProfile

        fields = (
            'notify_product_updates',
            'notify_email_addresses',
            'notify_expiry',
            'notify_cipher_preferences',
            'notify_short_id_usage',
            'enable_ical',
        )

        labels = {
            'notify_product_updates': (
                'Receive occasional emails announcing new features'
            ),

            'notify_email_addresses': (
                'Tell me about new PGP keys with my email address'
            ),

            'notify_expiry': (
                'Email me before my keys expire'
            ),

            'notify_cipher_preferences': (
                'Notify me when my cipher preferences are considered insecure'
            ),

            'notify_short_id_usage': (
                'Notify me about keyserver searches using my short ID'
            ),

            'enable_ical': (
                'Create a calendar feed (ical) for my key expiry dates'
            ),
        }

    extra_attrs = {
        'notify_expiry': {
            'disabled': '',
        },
        'notify_cipher_preferences': {
            'disabled': '',
        },
        'notify_short_id_usage': {
            'disabled': '',
        },
        'enable_ical': {
            'disabled': '',
        },
    }

    def clean_notify_expiry(self):  # disable updating this field
        if self.instance:
            return self.instance.notify_expiry
        else:
            return self.fields['sku']

    def clean_notify_cipher_preferences(self):  # disable updating this field
        if self.instance:
            return self.instance.notify_cipher_preferences
        else:
            return self.fields['sku']

    def clean_notify_short_id_usage(self):  # disable updating this field
        if self.instance:
            return self.instance.notify_short_id_usage
        else:
            return self.fields['sku']

    def clean_enable_ical(self):  # disable updating this field
        if self.instance:
            return self.instance.enable_ical
        else:
            return self.fields['sku']
