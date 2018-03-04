import datetime
import logging
import re

from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from expirybot.apps.keys.helpers import get_key, NoSuchKeyError, run_tests_task
from expirybot.apps.users.forms import MonitorEmailAddressForm

from .models import KeyTestResult


LOG = logging.getLogger(__name__)


class PGPKeyDetailView(TemplateView):
    template_name = 'keys/pgp_key_detail.html'
    model = PGPKey
    context_object_name = 'key'

    def get(self, *args, **kwargs):

        fingerprint = self.kwargs['pk']
        two_minutes = datetime.timedelta(minutes=2)

        try:
            pgp_key = get_key(fingerprint, max_staleness=two_minutes)

        except NoSuchKeyError:
            return HttpResponse(status=404)  # TODO - improve this UX

        alerts = pgp_key.alerts

        danger = list(filter(lambda a: a.severity == 'danger', alerts))
        warning = list(filter(lambda a: a.severity == 'warning', alerts))

        return self.render_to_response(
            {
                'key': pgp_key,
                'danger_alerts': danger,
                'warning_alerts': warning,
                'form': MonitorEmailAddressForm(),
            }
        )


class TestPGPKeyView(TemplateView):
    template_name = 'keys/test_pgp_key.html'

    def post(self, request, *args, **kwargs):
        ascii_key = request.POST['public-key'].strip()

        validate_key(ascii_key)  # blow up if invalid. OK for now.

        test_result = KeyTestResult.objects.create()

        # TODO: convert into a background job to process ascii_key and update
        #       test_result (calling set_test_result('test_id', <pass/fail>)

        run_tests_task(ascii_key, test_result)

        return redirect(reverse(
            'keys.key-test-result',
            kwargs={'pk': test_result.uuid}
        ))


class KeyTestResultView(DetailView):
    template_name = 'keys/key_test_result.html'
    model = KeyTestResult
    context_object_name = 'result'


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
