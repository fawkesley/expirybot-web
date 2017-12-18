from django.db import models

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.libs.uid_parser import parse_email_from_uid


class PGPKey(models.Model):

    fingerprint = models.CharField(
        help_text=(
            "The 40-character key fingerprint without spaces."
        ),
        max_length=40,
        primary_key=True,
    )

    key_algorithm = models.CharField(
        max_length=10,
        choices=(
            ('DSA', 'DSA (1)'),
            ('RSA-SIGN', 'RSA Sign-only (3)'),
            ('ELGAMAL', 'ELGAMAL (16)'),
            ('RSA', 'RSA (17)'),
            ('ECC', 'ECC (18)'),
            ('ECDSA', 'ECDSA (19)'),
        )
    )

    key_length_bits = models.PositiveSmallIntegerField()

    last_synced = models.DateTimeField(null=True, blank=True)

    creation_datetime = models.DateTimeField(null=True, blank=True)

    expiry_datetime = models.DateTimeField(null=True, blank=True)

    @property
    def human_fingerprint(self):
        return '{} {} {} {} {}  {} {} {} {} {}'.format(
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


class UID(models.Model):
    id = models.AutoField(primary_key=True)

    uid_string = models.CharField(max_length=500, db_index=True)

    key = models.ForeignKey(PGPKey, related_name='uids')

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
