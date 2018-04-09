import logging
import jwt

from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth import login
from django.shortcuts import redirect, resolve_url
from django.urls import reverse

from ..models import UserProfile

LOG = logging.getLogger(__name__)


class OneClickConfigView(TemplateView):
    template_name = 'users/one_click_config.html'

    class TokenError(Exception):
        pass

    def get(self, request, *args, **kwargs):
        try:
            self._validate_jwt(self.kwargs['json_web_token'])

        except self.TokenError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        try:
            (profile, config_key, config_value) = self._validate_jwt(
                self.kwargs['json_web_token']
            )

            self._set_config_value(profile, config_key, config_value)

        except self.TokenError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            url = reverse('users.settings')
            return redirect(url or resolve_url(settings.LOGIN_REDIRECT_URL))

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.DecodeError:
            LOG.error("Got invalid config JWT: {}".format(json_web_token))
            raise self.TokenError('The link appears to be invalid')

        except jwt.ExpiredSignatureError:
            LOG.warn("Got expired config JWT: {}".format(json_web_token))
            raise self.TokenError('The link has expired')

        else:
            if data['a'] != 'one-click-config':
                LOG.error("Got suspicious one-click-config JWT: {}".format(
                    json_web_token))

                raise self.TokenError('The link appears to be invalid')

        try:
            profile = UserProfile.objects.get(uuid=data['u'])
        except UserProfile.DoesNotExist:
            LOG.error("Got valid login JWT for non-existent user profile "
                      "{}".format(data))
            raise self.TokenError('The user was not found')

        return (profile, data.get('k', ''), data.get('v'))

    def _set_config_value(self, profile, config_key, config_value):
        user = profile.user
        if not user.is_active:
            LOG.error("Got valid config JWT for inactive user {}".format(user))
            raise self.TokenError('User is inactive')

        if config_key not in UserProfile.ALLOWED_ONE_CLICK_SETTINGS:
            LOG.error("Got valid config JWT with bad config_key "
                      "`{}`".format(config_key))
            raise self.TokenError('Something was wrong with the link')

        setattr(profile, config_key, config_value)
        profile.save()

        login(self.request, user)
