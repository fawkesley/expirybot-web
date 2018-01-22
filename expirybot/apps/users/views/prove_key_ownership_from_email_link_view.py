import logging

import jwt

from django.conf import settings

from django.views.generic import TemplateView

from expirybot.apps.keys.helpers import get_key

from ..models import UserProfile, KeyOwnershipProof

LOG = logging.getLogger(__name__)


class ProveKeyOwnershipFromEmailLinkView(TemplateView):
    template_name = 'users/prove_key_ownership_from_email_link.html'

    class ProveError(ValueError):
        pass

    def get(self, request, *args, **kwargs):
        try:
            (pgp_key, profile) = self._validate_jwt(
                self.kwargs['json_web_token']
            )
            self.add_key_to_profile(pgp_key, profile)

        except self.ProveError as e:
            return self.render_to_response({'error_message': str(e)})

        else:
            return self.render_to_response({})

    def _validate_jwt(self, json_web_token):
        try:
            data = jwt.decode(json_web_token, settings.SECRET_KEY)

        except jwt.ExpiredSignatureError:
            LOG.warn("Got expired JSON web token for user {}".format(
                self.request.user.username))
            raise self.ProveError('The link has expired')

        except jwt.DecodeError:
            LOG.error("Got invalid JSON web token for user {}: {}".format(
                self.request.user.username, json_web_token))
            raise self.ProveError('The link appears to be invalid')

        else:
            if data['a'] != 'prove-key':
                LOG.error(
                    "Got suspicious JSON web token on add-email for "
                    "user {}: {}".format(self.request.user.username, data)
                )

                raise self.ProveError('The link appears to be invalid')

        try:
            pgp_key = get_key(data['f'])
        except Exception:
            LOG.error('Failed to load PGP key {}'.format(data))
            raise self.ProveError('Failed to connect PGP key')

        try:
            profile = UserProfile.objects.get(uuid=data['u'])
        except UserProfile.DoesNotExist:
            raise self.ProveError(
                'The user was not found')

        return (pgp_key, profile)

    def add_key_to_profile(self, pgp_key, profile):

        try:
            existing_proof = KeyOwnershipProof.objects.get(pgp_key=pgp_key)

        except KeyOwnershipProof.DoesNotExist:
            KeyOwnershipProof.objects.create(
                pgp_key=pgp_key,
                profile=profile
            )
            LOG.warn('Key {} proven by {}'.format(pgp_key, profile))

        else:
            if existing_proof.profile != profile:
                LOG.error('Key {} already owned by {}'.format(
                    pgp_key, existing_proof.profile))

                raise self.ProveError('Key already belongs to someone else')
