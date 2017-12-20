from django.core.mail import send_mail


def send_validation_email(email_address, validation_url):
    body = 'Please click the following link:\n\n{}'.format(validation_url)

    send_mail(
        '[Expirybot] Confirm your email address',
        body,
        'bot@mail.expirybot.com',
        [email_address],
        fail_silently=False,
    )
