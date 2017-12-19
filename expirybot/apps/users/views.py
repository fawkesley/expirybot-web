from django.views.generic import TemplateView


class MonitorEmailAddressView(TemplateView):
    template_name = 'users/monitor_email_address.html'

    def post(self, request, *args, **kwargs):
        raise RuntimeError('{} {}'.format(args, kwargs))
