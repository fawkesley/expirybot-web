import datetime
import logging

import jwt

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse
from django.utils import timezone
from django.views.generic import DetailView

from expirybot.apps.keys.models import PGPKey
from expirybot.libs.gpg_wrapper import encrypt_message, GPGError

LOG = logging.getLogger(__name__)


class ProveKeyOwnershipView(LoginRequiredMixin, DetailView):
    template_name = 'users/prove_key_ownership.html'
    model = PGPKey
    context_object_name = 'pgp_key'

    def get_context_data(self, *args, **kwargs):
        pgp_key = kwargs.pop('object')

        ctx = super().get_context_data(*args, **kwargs)

        try:
            pgp_message = self.make_pgp_message(pgp_key)

        except GPGError as e:
            LOG.error(e)
            ctx.update({'error': True})

        else:
            ctx.update({
                'pgp_message': pgp_message
            })
        return ctx

    def make_pgp_message(self, key):
        plaintext = (
            "Hello!"
            "\n\n"
            "Please click the following link to prove you can access this key:"
            "\n\n"
            "{}\n\n").format(self.make_proof_url(key.fingerprint))

        return encrypt_message(key.fingerprint, plaintext)

    def make_proof_url(self, fingerprint):
        jwt_data = {
            'exp': timezone.now() + datetime.timedelta(days=7),
            'a': 'prove-key',
            'f': fingerprint,
            'u': str(self.request.user.profile.uuid),
        }

        proof_url = self.request.build_absolute_uri(
            reverse(
                'users.prove-key-ownership-from-email-link',
                kwargs={
                    'json_web_token': jwt.encode(jwt_data, settings.SECRET_KEY)
                }
            )
        )

        return proof_url
