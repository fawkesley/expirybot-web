import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from expirybot.apps.keys.models import KeyTestResult

LOG = logging.getLogger(__name__)


OLDER_THAN = datetime.timedelta(hours=12)


class Command(BaseCommand):
    help = ('Updates keys from the keyserver')

    def handle(self, *args, **options):
        delete_old_test_results()


def delete_old_test_results(now=None):
    now = now or timezone.now()

    to_delete = KeyTestResult.objects.filter(created_at__lt=now - OLDER_THAN)

    num_deleted = to_delete.count()

    to_delete.delete()

    LOG.info("Deleted {} old test results".format(num_deleted))
