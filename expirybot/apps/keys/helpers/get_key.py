import datetime

from django.utils import timezone

from expirybot.apps.keys.models import PGPKey
from .sync_key import sync_key


def get_key(fingerprint, max_staleness=None):
    """
    Return a reasonably up-to-date key, where max_staleness is a timedelta.
    """

    max_staleness = max_staleness or datetime.timedelta(hours=24)

    key, new = PGPKey.objects.get_or_create(fingerprint=fingerprint)

    def never_synced(key):
        return key.last_synced is None

    def is_stale(key):
        return (timezone.now() - key.last_synced) > max_staleness

    if new or never_synced(key) or is_stale(key):
        sync_key(key)

    return key
