from django.db import models

from django.contrib.postgres.fields import ArrayField

from .pgp_key import PGPKey
from .cryptographic_key import CryptographicKey
from .mixins import ExpiryCalculationMixin


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
        return {
            'long_id': self.long_id,
            'key_algorithm': self.key_algorithm,
            'key_length_bits': self.key_length_bits,
            'ecc_curve': self.ecc_curve,
            'creation_date': self.creation_date,
            'expiry_date': self.expiry_date,
            'revoked': self.revoked,
            'capabilities': self.capabilities,
        }
