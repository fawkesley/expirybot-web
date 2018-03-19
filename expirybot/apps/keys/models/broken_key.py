from django.core.exceptions import ValidationError
from django.db import models

from .cryptographic_key import CryptographicKey
from .mixins import FingerprintFormatMixin


class BrokenKey(models.Model, FingerprintFormatMixin):

    fingerprint = models.CharField(
        help_text=(
            "The 40-character key fingerprint without spaces."
        ),
        max_length=40,
        primary_key=True,
    )

    next_retry_sync = models.DateTimeField()

    def __str__(self):
        return self.zero_x_fingerprint
