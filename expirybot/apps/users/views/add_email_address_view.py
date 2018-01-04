import logging

import jwt

from django.conf import settings
from django.contrib.auth import login

from django.views.generic import TemplateView

from expirybot.apps.blacklist.models import EmailAddress

from ..forms import MonitorEmailAddressForm
from ..models import EmailAddressOwnershipProof, UserProfile
from ..utils import make_user_permanent

LOG = logging.getLogger(__name__)


class AddEmailAddressView(TemplateView):
    template_name = 'users/add_email_address.html'

    class AddEmailError(ValueError):
        pass

    def get(self, request, *args, **kwargs):
        try:
            (email, profile) = self._validate_jwt(
                self.kwargs['json_web_token']
            )
            self._add_email_address_to_profile(email, profile)

        except self.AddEmailError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            self._login_user_if_not_logged_in(profile.user)

            return self.render_to_response({
                'email_address': email,
                'user': profile.user,
                'form': MonitorEmailAddressForm()
            })

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.ExpiredSignatureError:
            LOG.warn("Got expired JSON web token for user {}".format(
                self.request.user.username))
            raise self.AddEmailError('The link has expired')

        except jwt.DecodeError:
            LOG.error("Got invalid JSON web token for user {}: {}".format(
                self.request.user.username, json_web_token))
            raise self.AddEmailError('The link appears to be invalid')

        else:
            if data['a'] != 'add-email':
                LOG.error(
                    "Got suspicious JSON web token on add-email for "
                    "user {}: {}".format(self.request.user.username, data)
                )

                raise self.AddEmailError('The link appears to be invalid')

        email = data['e']
        try:
            profile = UserProfile.objects.get(uuid=data['u'])
        except UserProfile.DoesNotExist:
            raise self.AddEmailError(
                'The user was not found')

        return (email, profile)

    def _add_email_address_to_profile(self, email_address, profile):
        user = profile.user

        (email_model, _) = EmailAddress.objects.get_or_create(
            email_address=email_address
        )

        try:
            existing_proof = EmailAddressOwnershipProof.objects.get(
                email_address=email_model
            )
        except EmailAddressOwnershipProof.DoesNotExist:
            existing_proof = None

        else:
            if existing_proof.profile != profile:
                LOG.warn(
                    "Prevented change of ownership of email address {} "
                    "from {} to {}".format(
                        email_address, email_model.owner_profile, profile)
                )

            raise self.AddEmailError(
                '{} is already being monitored'.format(email_address)
            )

        if existing_proof is None:
            EmailAddressOwnershipProof.objects.create(
                profile=profile,
                email_address=email_model
            )

        if user.profile.is_temporary:
            make_user_permanent(user, email_address)

    def _login_user_if_not_logged_in(self, user):
        if self.request.user.is_anonymous():
            login(self.request, user)
