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
    # Required until migration 0010 is squashed
    pass


class ExpiryCalculationMixin():
    @property
    def expires(self):
        return self.expiry_date is not None

    @property
    def has_expired(self):
        return self.expires and self.expiry_date < timezone.now().date()


class CryptographicKey(models.Model):
    ALGORITHM_CHOICES = (
        ('', 'Unknown'),

        # https://tools.ietf.org/html/rfc4880#section-9.1
        ('RSA', 'RSA (1)'),
        ('RSA-ENCRYPT', 'RSA Encrypt-only (2)'),
        ('RSA-SIGN', 'RSA Sign-only (3)'),
        ('ELGAMAL', 'ELGAMAL (Encrypt-only) (16)'),
        ('DSA', 'DSA (17)'),

        ('ECC', 'Elliptic curve - ECDH encrypt / ECDSA sign (18/19)'),

        # Technically ECC should be one of the following, but does it matter
        # for my purposes?
        #
        # https://tools.ietf.org/html/rfc6637#section-5
        # ('ECDH', 'Elliptic Curve Diffie Hillman - encrypt (18)'),
        # ('ECDSA', 'ECDSA public key algorithm - signing (19)'),
    )

    CAPABILITY_CHOICES = (
        # https://tools.ietf.org/html/rfc4880#section-5.2.3.21

        ('C', 'certifying other keys'),      # 0x01
        ('S', 'signing data'),               # 0x02
        ('E', 'encrypting data'),            # 0x04 or 0x08
        ('A', 'authenticating'),             # 0x20
    )

    ECC_CURVE_CHOICES = (
        # https://tools.ietf.org/html/rfc6637#section-12.1
        # https://gnupg.org/faq/whats-new-in-2.1.html

        ('', 'Unknown'),

        ('ed25519', 'Ed25519 (sign only)'),        # ECDSA - signing only
        ('cv25519', 'Curve25519 (encrypt only)'),  # ECDH - encryption only

        ('nistp256', 'NIST P-256'),
        ('nistp384', 'NIST P-384'),
        ('nistp521', 'NIST P-521'),

        ('brainpoolP256r1', 'Brainpool P-256'),
        ('brainpoolP384r1', 'Brainpool P-384'),
        ('brainpoolP512r1', 'Brainpool P-512'),

        ('secp256k1', 'secp256k1 (sign only)')  # ECDSA - signing
    )

    class Meta:
        abstract = True  # https://docs.djangoproject.com/en/1.11/topics/db/models/#abstract-base-classes  # noqa

    key_algorithm = models.CharField(
        null=False, blank=True,
        max_length=20,
        choices=ALGORITHM_CHOICES
    )

    key_length_bits = models.PositiveIntegerField(
        null=True, blank=True,
    )

    capabilities = ArrayField(
        base_field=models.CharField(
            max_length=1,
            choices=CAPABILITY_CHOICES,
        ),
        null=False,
        blank=True,
        default=[]
    )

    ecc_curve = models.CharField(
        null=False,
        blank=True,
        default='',
        max_length=100,
        choices=ECC_CURVE_CHOICES
    )

    def friendly_capabilities(self):
        lookup = dict(PGPKey.CAPABILITY_CHOICES)

        return [lookup[c] for c in self.capabilities]

    def friendly_type(self):
        """
        Return a friendly name describing the key type
        """

        types_with_key_length = set(
            ['RSA', 'RSA-ENCRYPT', 'RSA-SIGN', 'DSA', 'ELGAMAL']
        )

        if self.key_algorithm in types_with_key_length:
            return '{}-bit {}'.format(self.key_length_bits, self.key_algorithm)

        elif self.key_algorithm == 'ECC':
            return 'Elliptic Curve ({})'.format(self.friendly_ecc_curve())

        elif not self.key_algorithm:
            return 'unknown'

    def friendly_ecc_curve(self):
        return dict(self.ECC_CURVE_CHOICES)[self.ecc_curve]


class PGPKey(CryptographicKey, ExpiryCalculationMixin):

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

    last_synced = models.DateTimeField(null=True, blank=True)

    creation_date = models.DateField(null=True, blank=False)

    expiry_date = models.DateField(null=True, blank=True)

    revoked = models.BooleanField(default=False)

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


class Subkey(CryptographicKey, ExpiryCalculationMixin):
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
