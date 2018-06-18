import datetime
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from expirybot.apps.status.models import EventLatestOccurrence

LOG = logging.getLogger(__name__)


OLDER_THAN = datetime.timedelta(hours=12)


class Command(BaseCommand):
    help = ("Delete old tmp-* users that haven't converted into real users")

    def handle(self, *args, **options):
        delete_unconfirmed_users()


def delete_unconfirmed_users(now=None):
    now = now or timezone.now()

    to_delete = User.objects.filter(
        username__startswith='tmp-',
        date_joined__lt=now - OLDER_THAN
    )

    num_deleted = to_delete.count()
    LOG.info('Deleting these users: {}'.format(
        ', '.join(u.username for u in to_delete))
    )

    LOG.info('NOT deleting yet')

    # TODO: enable this
    # to_delete.delete()
    # LOG.info("Deleted {} old users".format(num_deleted))
    # EventLatestOccurrence.record_event('delete-unconfirmed-users-succeeded')
