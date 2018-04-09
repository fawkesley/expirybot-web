import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader

from expirybot.apps.blacklist.utils import (
    allow_send_email, make_authenticated_unsubscribe_url
)

LOG = logging.getLogger(__name__)


def send_validation_email(email_address, validation_url):
    send_email(
        email_address,
        'verify_email',
        {
            "validation_url": validation_url,
        }
    )


def send_initial_email_monitoring_email(email_address, fingerprints):
    send_email(
        email_address,
        'email_monitoring_initial',
        {
            'fingerprints': fingerprints
        },
        cc_admin=True,
    )


def send_new_key_email_monitoring_email(email_address, fingerprints_added):
    send_email(
        email_address,
        'email_monitoring_new_key',
        {
            'fingerprints_added': fingerprints_added,
        },
        cc_admin=True,
    )


def send_login_email(email_address, login_url):
    send_email(
        email_address,
        'login',
        {
            "login_url": login_url,
        },
        cc_admin=True,
    )


def send_email(email_address, template_fn, context, cc_admin=False):
    assert isinstance(email_address, str), type(email_address)
    LOG.info('Sending email {} : {} context={}'.format(
        email_address, template_fn, context
    ))

    if not allow_send_email(email_address):
        raise RuntimeError(
            "Tried to email blacklisted address/domain: {}".format(
                email_address)
        )

    body_template = loader.get_template(
        'email/{}_body.txt'.format(template_fn)
    )

    subject_template = loader.get_template(
        'email/{}_subject.txt'.format(template_fn)
    )

    context.update({
        "email_address": email_address,
        "unsubscribe_url": '{base_url}{path}'.format(
            base_url=settings.EXPIRYBOT_BASE_URL,
            path=make_authenticated_unsubscribe_url(email_address),
        )
    })

    body = body_template.render(context)
    subject = '[Expirybot] {}'.format(subject_template.render(context)).strip()

    from_address = '"Expirybot" <bot@mail.expirybot.com>'

    recipient_list = [email_address]

    if cc_admin:
        bcc_list = ['bcc-expirybot-{}@paulfurley.com'.format(template_fn)]
    else:
        bcc_list = []

    email = EmailMessage(
        subject, body, from_address, recipient_list,
        bcc_list,
        reply_to=['paul@paulfurley.com'],
    )
    email.send()
