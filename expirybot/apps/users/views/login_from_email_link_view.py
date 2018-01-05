import logging
import jwt

from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth import login
from django.shortcuts import redirect, resolve_url

from ..models import UserProfile

from .mixins import GetRedirectUrlMixin

LOG = logging.getLogger(__name__)


class LoginFromEmailLinkView(GetRedirectUrlMixin, TemplateView):
    template_name = 'users/login_from_email_link.html'

    class LoginError(Exception):
        pass

    def get(self, request, *args, **kwargs):
        try:
            user, next_url = self._validate_jwt(self.kwargs['json_web_token'])

        except self.LoginError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            return self.render_to_response({
                'login_user': user,
                'next': next_url,
            })

    def post(self, request, *args, **kwargs):
        try:
            user, _ = self._validate_jwt(self.kwargs['json_web_token'])
            self._login_as(user)

        except self.LoginError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            url = self.get_redirect_url()
            return redirect(url or resolve_url(settings.LOGIN_REDIRECT_URL))

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.DecodeError:
            LOG.error("Got invalid login JWT: {}".format(json_web_token))
            raise self.LoginError('The link appears to be invalid')

        except jwt.ExpiredSignatureError:
            LOG.warn("Got expired login JWT: {}".format(json_web_token))
            raise self.LoginError('The link has expired')

        else:
            if data['a'] != 'login':
                LOG.error("Got suspicious login JWT: {}".format(
                    json_web_token))

                raise self.LoginError('The link appears to be invalid')

        try:
            profile = UserProfile.objects.get(uuid=data['u'])
        except UserProfile.DoesNotExist:
            LOG.error("Got valid login JWT for non-existent user profile "
                      "{}".format(data))
            raise self.LoginError('The user was not found')

        return (profile.user, data.get('n', ''))

    def _login_as(self, user):
        if not user.is_active:
            LOG.error("Got valid login JWT for inactive user {}".format(user))
            raise self.LoginError('User is inactive')

        login(self.request, user)
