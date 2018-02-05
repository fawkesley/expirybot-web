import datetime

from django.utils import timezone
from django.db import transaction

from expirybot.apps.keys.models import PGPKey
from .sync_key import sync_key


def get_key(fingerprint, max_staleness=None):
    """
    Return a reasonably up-to-date key, where max_staleness is a timedelta.
    If the fingerprint was invalid, the key won't be saved.
    """

    max_staleness = max_staleness or datetime.timedelta(hours=24)

    def never_synced(key):
        return key.last_synced is None

    def is_stale(key):
        return (timezone.now() - key.last_synced) > max_staleness

    with transaction.atomic():
        key, new = PGPKey.objects.get_or_create(fingerprint=fingerprint)

        if new or never_synced(key) or is_stale(key):
            sync_key(key)

    return key
