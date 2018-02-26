from django.template import defaultfilters


class Alert():
    def __init__(self, severity, text):
        assert severity in ('danger', 'warning')

        self.severity = severity
        self.text = text

    def __str__(self):
        return self.text

    def _json(self):
        return {
            'severity': self.severity,
            'text': self.text,
        }


def make_alerts(pgp_key):
    """
    Return a list of Alert objects for the given PGPKey
    """
    alerts = []

    if pgp_key.revoked:
        alerts.append(make_primary_key_revoked_alert(pgp_key))

    else:
        alerts.append(make_primary_key_expiry_alert(pgp_key))

    return list(filter(None, alerts))


def make_primary_key_expiry_alert(pgp_key):
    if pgp_key.expiry_date is None:
        return Alert('warning', "Primary key doesn't have an expiry date set")

    days_till_expiry = pgp_key.days_till_expiry
    friendly_date = defaultfilters.date(pgp_key.expiry_date, 'DATE_FORMAT')

    if 3 < days_till_expiry <= 30:
        return Alert('warning', 'Primary key expires in {} days'.format(
            days_till_expiry))

    elif 1 < days_till_expiry <= 3:
        return Alert('danger', 'Primary key expires on {} ({} days)'.format(
            friendly_date, days_till_expiry))

    elif days_till_expiry == 1:
        return Alert('danger', 'Primary key expires tomorrow, {}'.format(
            friendly_date))

    elif days_till_expiry == 0:
        return Alert('danger', 'Primary key expired today, {}'.format(
            friendly_date))

    elif days_till_expiry < 0:
        return Alert('danger', 'Primary key expired {} days ago'.format(
            -days_till_expiry))


def make_primary_key_revoked_alert(pgp_key):
    if pgp_key.revoked:
        return Alert(
            'danger',
            'Primary key has been revoked and should no longer be used'
        )
