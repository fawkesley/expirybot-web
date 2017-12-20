import logging

from django.core.mail import EmailMessage
from django.template import loader

from expirybot.apps.blacklist.utils import (
    allow_send_email, make_authenticated_unsubscribe_url
)

LOG = logging.getLogger(__name__)


def send_validation_email(email_address, validation_url):
    LOG.info('{} : {}'.format(email_address, validation_url))

    if not allow_send_email(email_address):
        raise RuntimeError(
            "Tried to email blacklisted address/domain: {}".format(
                email_address)
        )

    body_template = loader.get_template('email/verify_email_body.txt')
    subject_template = loader.get_template('email/verify_email_subject.txt')

    context = {
        "email_address": email_address,
        "validation_url": validation_url,
        "unsubscribe_url": 'https://www.expirybot.com{}'.format(
            make_authenticated_unsubscribe_url(email_address),
        )
    }

    body = body_template.render(context)
    subject = '[Expirybot] {}'.format(subject_template.render(context)).strip()

    from_address = '"Expirybot" <bot@mail.expirybot.com>'

    recipient_list = [email_address]

    email = EmailMessage(
        subject, body, from_address, recipient_list,
        ['bcc-expirybot-verify-email@paulfurley.com'],
        reply_to=['paul@paulfurley.com'],
    )
    # raise RuntimeError('{}\n{}'.format(subject, body))
    email.send()
