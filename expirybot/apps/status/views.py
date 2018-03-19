from django.views.generic import TemplateView

from expirybot.apps.keys.models import PGPKey


class StatusView(TemplateView):
    template_name = 'status/status.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        num_keys = PGPKey.objects.all().count()

        ctx.update({
            'num_keys': num_keys
        })
        return ctx
