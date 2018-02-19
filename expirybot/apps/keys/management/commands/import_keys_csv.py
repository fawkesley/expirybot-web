import csv
import datetime
import io
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from expirybot.apps.keys.models import (
    PGPKey, UID
)

LOG = logging.getLogger(__name__)


ALGOS = {
    1: 'RSA',
    3: 'RSA-SIGN',
    16: 'ELGAMAL',
    17: 'DSA',
    18: 'ECC',
    19: 'ECDSA',
}


class Command(BaseCommand):
    help = ('Updates keys from the keyserver')

    def handle(self, *args, **options):
        import_keys()


def import_keys():

    csv.field_size_limit(500 * 1024 * 1024)

    with io.open('keys.csv', 'r') as f:
        counter = 0

        for row in csv.DictReader(f):
            if is_valid_and_recent(row):
                create_key(row)

            counter += 1
            if counter % 10000 == 0:
                print(counter)


def create_key(row):
    fingerprint = row['fingerprint'].replace(' ', '').upper()

    with transaction.atomic():
        try:
            create_key_now(
                fingerprint,
                ALGOS[int(row['algorithm_number'])],
                int(row['size_bits'])
            )
        except Exception:
            print("failed: {}".format(row))


def create_key_now(fingerprint, algorithm_name, size_bits):

    (key, was_created) = PGPKey.objects.get_or_create(
        fingerprint=fingerprint,
        defaults={
            'key_algorithm': algorithm_name,
            'key_length_bits': size_bits,
        }
    )

    return key


def update_uids(key, uid_strings):
    UID.objects.filter(key=key).delete()

    for uid_string in uid_strings:
        UID.objects.create(
            key=key,
            uid_string=uid_string
        )


def is_valid_and_recent(row):
    if has_expiry_date(row):
        return not_expired(row)
    else:
        return created_within_5_years(row)


def has_expiry_date(row):
    return bool(row['expiry_date'])


def created_within_5_years(row):
    created_date = row['created_date']

    five_years_ago = datetime.date.today() - datetime.timedelta(days=5*356)

    if parse_date(created_date) > five_years_ago:
        # print('{} is within 5 years'.format(created_date))
        return True


def not_expired(row):
    expiry_date = row['expiry_date']

    if parse_date(expiry_date) > datetime.date.today():
        # print('{} is not expired'.format(expiry_date))
        return True


def parse_date(date_string):
    year, month, date = map(int, date_string.split('-'))

    return datetime.date(year, month, date)
