import datetime

from django.utils import timezone

from .sync_key import sync_key


def get_key(fingerprint, max_staleness=None):
    """
    Return a reasonably up-to-date key, where max_staleness is a timedelta.
    If the fingerprint was invalid, the key won't be saved.

    This can raise NoSuchKeyError and KeyParsingError
    """

    from expirybot.apps.keys.models import PGPKey

    max_staleness = max_staleness or datetime.timedelta(hours=24)

    def never_synced(key):
        return key.last_synced is None

    def is_stale(key):
        return (timezone.now() - key.last_synced) > max_staleness

    try:
        key = PGPKey.objects.get(fingerprint=fingerprint)

    except PGPKey.DoesNotExist:
        key = _create_key(fingerprint)

    else:
        if never_synced(key) or is_stale(key):
            sync_key(key)

    return key


def _create_key(fingerprint):
    from expirybot.apps.keys.models import PGPKey

    key = PGPKey(fingerprint=fingerprint)  # don't auto-save
    sync_key(key)
    return key
