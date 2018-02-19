import re

from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django.contrib.postgres.fields import ArrayField

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.libs.uid_parser import parse_email_from_uid


def validate_fingerprint(string):
    def validate_openpgp_v4_fingerprint(string):
        return bool(re.match('^[A-F0-9]{40}$', string))

    def validate_openpgp_v3_fingerprint(string):
        return bool(re.match('^[A-F0-9]{16}$', string))

    if not validate_openpgp_v4_fingerprint(string) \
            and not validate_openpgp_v3_fingerprint(string):
        raise ValidationError('Not an OpenPGP v3 or v4 fingerprint: {}'.format(
            string))


class FriendlyCapabilitiesMixin():
    def friendly_capabilities(self):
        lookup = dict(PGPKey.CAPABILITY_CHOICES)

        return [lookup[c] for c in self.capabilities]


class ExpiryCalculationMixin():
    @property
    def expires(self):
        return self.expiry_date is not None

    @property
    def has_expired(self):
        return self.expires and self.expiry_date < timezone.now().date()


class PGPKey(models.Model, FriendlyCapabilitiesMixin, ExpiryCalculationMixin):

    ALGORITHM_CHOICES = (
        ('DSA', 'DSA (1)'),
        ('RSA-SIGN', 'RSA Sign-only (3)'),
        ('ELGAMAL', 'ELGAMAL (16)'),
        ('RSA', 'RSA (17)'),
        ('ECC', 'ECC (18)'),
        ('ECDSA', 'ECDSA (19)'),
        ('', 'Unknown'),
    )

    CAPABILITY_CHOICES = (
        # https://tools.ietf.org/html/rfc4880#section-5.2.3.21

        ('C', 'certifying other keys'),      # 0x01
        ('S', 'signing data'),               # 0x02
        ('E', 'encrypting data'),            # 0x04 or 0x08
        ('A', 'authenticating'),             # 0x20
    )

    fingerprint = models.CharField(
        help_text=(
            "The 40-character key fingerprint without spaces."
        ),
        max_length=40,
        primary_key=True,
        validators=[
            validate_fingerprint,
        ],
    )

    key_algorithm = models.CharField(
        null=False, blank=True,
        max_length=10,
        choices=ALGORITHM_CHOICES
    )

    key_length_bits = models.PositiveIntegerField(
        null=True, blank=True,
    )

    last_synced = models.DateTimeField(null=True, blank=True)

    creation_date = models.DateField(null=True, blank=False)

    expiry_date = models.DateField(null=True, blank=True)

    revoked = models.BooleanField(default=False)

    capabilities = ArrayField(
        base_field=models.CharField(
            max_length=1,
            choices=CAPABILITY_CHOICES,
        ),
        null=False,
        blank=True,
        default=[]
    )

    @property
    def human_fingerprint(self):
        if len(self.fingerprint) == 40:
            return '{} {} {} {} {}  {} {} {} {} {}'.format(  # nbsp
                self.fingerprint[0:4],
                self.fingerprint[4:8],
                self.fingerprint[8:12],
                self.fingerprint[12:16],
                self.fingerprint[16:20],
                self.fingerprint[20:24],
                self.fingerprint[24:28],
                self.fingerprint[28:32],
                self.fingerprint[32:36],
                self.fingerprint[36:40]
            )
        else:
            return self.fingerprint

    def __str__(self):
        return self.zero_x_fingerprint

    @property
    def zero_x_fingerprint(self):
        return '0x{}'.format(self.fingerprint)

    @property
    def key_id(self):
        return '0x{}'.format(self.fingerprint[-16:])

    @property
    def uids_string(self):
        return ', '.join(str(uid) for uid in self.uids.all())

    @property
    def email_addresses(self):
        return list(filter(
            None,
            (uid.email_address for uid in self.uids.all())
        ))

    @property
    def uids(self):
        return self.uids_set.all()

    @property
    def subkeys(self):
        return self.subkeys_set.all()


class UID(models.Model):
    id = models.AutoField(primary_key=True)

    uid_string = models.CharField(max_length=500, db_index=True)

    key = models.ForeignKey(PGPKey, related_name='uids_set')

    email_address = models.ForeignKey(
        EmailAddress,
        null=True,
        related_name='uids'
    )

    @property
    def email_address(self):
        email_address = parse_email_from_uid(self.uid_string)
        obj, _ = EmailAddress.objects.get_or_create(
            email_address=email_address
        )
        return obj

    def __str__(self):
        return self.uid_string


class Subkey(models.Model, FriendlyCapabilitiesMixin, ExpiryCalculationMixin):
    id = models.AutoField(primary_key=True)

    long_id = models.CharField(max_length=16)

    key = models.ForeignKey(PGPKey, related_name='subkeys_set')

    key_algorithm = models.CharField(
        null=False,
        blank=True,
        max_length=10,
        choices=PGPKey.ALGORITHM_CHOICES
    )

    key_length_bits = models.PositiveIntegerField(
        null=True, blank=True,
    )

    creation_date = models.DateField(null=False)

    expiry_date = models.DateField(null=True, blank=True)

    revoked = models.BooleanField(default=False)

    capabilities = ArrayField(
        base_field=models.CharField(
            max_length=1,
            choices=PGPKey.CAPABILITY_CHOICES,
        ),
        null=False,
        blank=True,
    )

    def to_dict(self):
        return OrderedDict([
            ('key_algorithm', self.key_algorithm),
            ('key_length_bits', self.key_length_bits),
            ('creation_date', self.creation_date),
            ('expiry_date', self.expiry_date),
            ('revoked', self.revoked),
            ('capabilities', self.capabilities),
        ])
