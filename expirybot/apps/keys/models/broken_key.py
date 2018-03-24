from django.db import models

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

    error_message = models.TextField(
        null=False,
        blank=True,
        default=''
    )

    def __str__(self):
        return self.zero_x_fingerprint
