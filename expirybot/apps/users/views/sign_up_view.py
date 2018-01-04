import logging

from django.conf import settings

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import (
    SuccessURLAllowedHostsMixin,
)

from django.shortcuts import resolve_url
from django.utils.http import is_safe_url

from django.views.generic.edit import FormView

LOG = logging.getLogger(__name__)


class SignUpView(SuccessURLAllowedHostsMixin, FormView):
    form_class = UserCreationForm
    template_name = 'users/sign_up.html'
    redirect_field_name = 'next'

    def form_valid(self, form):
        form.save()  # save the new user first

        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']

        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(SignUpView, self).form_valid(form)

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""

        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            self.redirect_field_name: self.get_redirect_url(),
        })
        return context
