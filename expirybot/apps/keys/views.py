import datetime
import logging

from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.http import HttpResponse


from expirybot.apps.keys.models import PGPKey
from expirybot.apps.keys.helpers import get_key, NoSuchKeyError
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


class KeyTestResultView(DetailView):
    template_name = 'keys/key_test_result.html'
    model = KeyTestResult
    context_object_name = 'result'
