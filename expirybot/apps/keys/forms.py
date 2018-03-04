import logging
import re

from django import forms
from django.forms import ValidationError
from expirybot.apps.keys.helpers import run_tests_task
from expirybot.libs.gpg_wrapper import GPGError
from .models import KeyTestResult


LOG = logging.getLogger(__name__)


class PublicKeyForm(forms.Form):
    public_key = forms.CharField(widget=forms.Textarea)

    def clean_public_key(self):
        ascii_key = self.cleaned_data['public_key']

        try:
            validate_key(ascii_key)  # blow up if invalid. OK for now.
        except ValueError as e:
            raise ValidationError(e)

        # TODO: convert into a background job to process ascii_key and update
        #       test_result (calling set_test_result('test_id', <pass/fail>)
        self.test_result = KeyTestResult.objects.create()

        try:
            run_tests_task(ascii_key, self.test_result)
        except GPGError as e:
            LOG.exception(e)
            raise ValidationError(
                'There was an error parsing the public key.')

        return ascii_key


def validate_key(ascii_key):

    PUBLIC_KEY_HEADER = '-----BEGIN PGP PUBLIC KEY BLOCK-----'
    PUBLIC_KEY_FOOTER = '-----END PGP PUBLIC KEY BLOCK-----'
    PRIVATE_KEY_HEADER = '-----BEGIN PGP PRIVATE KEY BLOCK-----'

    if PRIVATE_KEY_HEADER in ascii_key:
        raise ValueError('Got private key!')

    if not ascii_key.startswith(PUBLIC_KEY_HEADER):
        raise ValueError("Missing PGP keader: {}".format(ascii_key))

    if not ascii_key.endswith(PUBLIC_KEY_FOOTER):
        raise ValueError('Missing PGP footer: {}'.format(ascii_key))

    if len(re.findall(PUBLIC_KEY_HEADER, ascii_key)) > 1:
        raise ValueError('Multiple PGP key headers found, expecting 1')
