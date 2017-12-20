from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin


from .forms import MonitorEmailAddressForm


class MonitorEmailAddressView(FormView):
    template_name = 'users/monitor_email_address.html'
    form_class = MonitorEmailAddressForm

    def form_valid(self, form):
        raise RuntimeError(form)

    def get_success_url(self):
        raise RuntimeError


class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'
