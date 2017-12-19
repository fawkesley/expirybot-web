from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class MonitorEmailAddressView(TemplateView):
    template_name = 'users/monitor_email_address.html'

    def post(self, request, *args, **kwargs):
        raise RuntimeError('{} {}'.format(args, kwargs))


class UserSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'
    redirect_field_name = 'redirect_to'
