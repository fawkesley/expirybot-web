from django.db import models
from django.contrib.postgres.fields import CIEmailField
from django.core.exceptions import ObjectDoesNotExist


class EmailAddress(models.Model):
    class Meta:
        permissions = (
            ("make_unsubscribe_links",
             "Can create unsubscribe links for email addresses."),
        )
    email_address = CIEmailField(primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    unsubscribe_datetime = models.DateTimeField(
        null=True,
        blank=True,
        default=None
    )

    complain_datetime = models.DateTimeField(
        null=True,
        blank=True,
        default=None
    )

    last_bounce_datetime = models.DateTimeField(
        null=True,
        blank=True,
        default=None
    )

    def __str__(self):
        return self.email_address

    def make_authenticated_unsubscribe_url(self):
        from .utils import make_authenticated_unsubscribe_url
        return make_authenticated_unsubscribe_url(self.email_address)

    @property
    def owner_profile(self):
        try:
            owner_proof = self.owner_proof

        except ObjectDoesNotExist:
            return None

        else:
            return owner_proof.profile


class BlacklistedDomain(models.Model):
    domain = models.CharField(
        primary_key=True,
        max_length=200
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.domain
