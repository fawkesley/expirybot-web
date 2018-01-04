import logging


from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import reverse

from django.views.generic.edit import UpdateView

from ..forms import UserSettingsForm
from ..models import UserProfile

LOG = logging.getLogger(__name__)


class UserSettingsView(LoginRequiredMixin, UpdateView):
    template_name = 'users/settings.html'
    form_class = UserSettingsForm
    model = UserProfile

    def get_object(self, *args, **kwargs):
        return self.request.user.profile

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Do any custom stuff here

        self.object.save()
        return super().form_valid(form)
        # render_to_response(self.template_name, self.get_context_data())

    def get_success_url(self, *args, **kwargs):
        return reverse('users.settings')
