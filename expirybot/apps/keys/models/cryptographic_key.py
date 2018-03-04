from django.db import models

from django.contrib.postgres.fields import ArrayField, JSONField
from .custom_json_encoder import CustomJSONEncoder


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

    alerts_json = JSONField(encoder=CustomJSONEncoder, default=list)

    @property
    def alerts(self):
        from .helpers.alerts import Alert

        def to_alert(dict_or_alert):
            if isinstance(dict_or_alert, Alert):
                return dict_or_alert
            else:
                return Alert(**dict_or_alert)

        return [to_alert(a) for a in self.alerts_json]

    @alerts.setter
    def alerts(self, value):
        assert isinstance(value, list), '{} type {}'.format(value, type(value))
        self.alerts_json = value

    def friendly_capabilities(self):
        lookup = dict(CryptographicKey.CAPABILITY_CHOICES)

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
