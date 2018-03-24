from django.db import models

from .mixins import FingerprintFormatMixin


class KeyUpdate(models.Model, FingerprintFormatMixin):
    """
    This corresponds to a SKS log message indicating a key has been updated
    in the database.
    """

    sks_hash = models.CharField(
        primary_key=True,
        max_length=32
    )

    updated_at = models.DateTimeField(
        db_index=True
    )

    fingerprint = models.CharField(
        help_text=(
            "The 40-character key fingerprint without spaces."
        ),
        max_length=40,
        db_index=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.zero_x_fingerprint
