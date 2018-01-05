import logging

from django.conf import settings

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm

from django.shortcuts import resolve_url

from django.views.generic.edit import FormView

from .mixins import GetRedirectUrlMixin

LOG = logging.getLogger(__name__)


class SignUpView(GetRedirectUrlMixin, FormView):
    form_class = UserCreationForm
    template_name = 'users/sign_up.html'

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            self.redirect_field_name: self.get_redirect_url(),
        })
        return context
