from django.db import models

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.libs.uid_parser import parse_email_from_uid

from .pgp_key import PGPKey


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
