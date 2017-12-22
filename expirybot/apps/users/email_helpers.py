import logging

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
        }
    )


def send_new_key_email_monitoring_email(email_address, fingerprints_added):
    send_email(
        email_address,
        'email_monitoring_new_key',
        {
            'fingerprints_added': fingerprints_added,
        }
    )


def send_email(email_address, template_fn, context):
    assert isinstance(email_address, str), type(email_address)
    LOG.info('{} : {} context={}'.format(email_address, template_fn, context))

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
        "unsubscribe_url": 'https://www.expirybot.com{}'.format(
            make_authenticated_unsubscribe_url(email_address),
        )
    })

    body = body_template.render(context)
    subject = '[Expirybot] {}'.format(subject_template.render(context)).strip()

    from_address = '"Expirybot" <bot@mail.expirybot.com>'

    recipient_list = [email_address]

    email = EmailMessage(
        subject, body, from_address, recipient_list,
        ['bcc-expirybot-{}@paulfurley.com'.format(template_fn)],
        reply_to=['paul@paulfurley.com'],
    )
    # raise RuntimeError('{}\n{}'.format(subject, body))
    email.send()
