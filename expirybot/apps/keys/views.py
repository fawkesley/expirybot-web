import datetime
import logging

from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.http import HttpResponse
from django.urls import reverse

from expirybot.apps.keys.helpers import get_key, NoSuchKeyError
from expirybot.apps.users.forms import MonitorEmailAddressForm

from .models import KeyTestResult
from .forms import PublicKeyForm


LOG = logging.getLogger(__name__)


class PGPKeyDetailView(TemplateView):
    template_name = 'keys/pgp_key_detail.html'

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


class TestPGPKeyView(FormView):
    template_name = 'keys/test_pgp_key.html'
    form_class = PublicKeyForm

    def form_valid(self, form):

        self.form = form

        return super(TestPGPKeyView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'keys.key-test-result',
            kwargs={'pk': self.form.test_result.uuid}
        )


class KeyTestResultView(DetailView):
    template_name = 'keys/key_test_result.html'
    model = KeyTestResult
    context_object_name = 'result'
