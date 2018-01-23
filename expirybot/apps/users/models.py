import logging
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.contrib.postgres.fields import ArrayField

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.apps.keys.models import PGPKey
from expirybot.apps.keys.helpers import get_key

LOG = logging.getLogger(__name__)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    uuid = models.UUIDField(
        unique=True,
        null=False,
        default=uuid.uuid4,
        editable=False,
    )

    notify_product_updates = models.BooleanField(default=True)

    notify_email_addresses = models.BooleanField(default=True)

    notify_expiry = models.BooleanField(default=True)
    notify_cipher_preferences = models.BooleanField(default=True)
    notify_short_id_usage = models.BooleanField(default=True)
    enable_ical = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

    @property
    def owned_email_addresses(self):
        return [
            proof.email_address
            for proof in self.email_address_ownership_proofs.all()
        ]

    @property
    def owned_pgp_keys(self):
        return [
            proof.pgp_key
            for proof in self.pgp_key_ownership_proofs.all()
        ]

    @property
    def is_temporary(self):
        return self.user.username.startswith('tmp-')

    @property
    def possible_pgp_keys(self):
        fingerprints = set()
        owned_fingerprints = set(k.fingerprint for k in self.owned_pgp_keys)

        for email in self.owned_email_addresses:
            try:
                search_results = SearchResultForKeysByEmail.objects.get(
                    email_address=email
                )
            except SearchResultForKeysByEmail.DoesNotExist:
                continue
            else:
                fingerprints.update(search_results.key_fingerprints)

        keys = []
        for f in sorted(fingerprints - owned_fingerprints):
            try:
                keys.append(get_key(f))
            except Exception as e:
                LOG.error(e)

        return keys


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)


class EmailAddressOwnershipProof(models.Model):
    email_address = models.OneToOneField(
        EmailAddress,
        related_name='owner_proof'
    )

    profile = models.ForeignKey(
        UserProfile,
        related_name='email_address_ownership_proofs'
    )

    def __str__(self):
        return '{} owns {}'.format(
            self.profile.user.username, self.email_address.email_address
        )


class KeyOwnershipProof(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    pgp_key = models.OneToOneField(
        PGPKey,
        related_name='owner_proof'
    )

    profile = models.ForeignKey(
        UserProfile,
        related_name='pgp_key_ownership_proofs'
    )

    def __str__(self):
        return '{} owns {}'.format(
            self.profile.user.username, self.pgp_key
        )


class SearchResultForKeysByEmail(models.Model):
    """
    Stores the result of searching the keyservers for an email address.
    """
    datetime = models.DateTimeField(auto_now_add=True)

    email_address = models.OneToOneField(
        EmailAddress,
        related_name='latest_search_by_email',
        null=True
    )

    key_fingerprints = ArrayField(
        base_field=models.CharField(max_length=40),
        null=False,
        blank=True,
    )
