import jwt

from django.conf import settings
from django.db import models
from django.urls import reverse


class BlacklistedEmailAddress(models.Model):
    email_address = models.EmailField(primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    unsubscribed = models.BooleanField(default=False)

    bounced = models.BooleanField(default=False)

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email_address

    def make_json_web_token(self):
        data = {
            'email_address': str(self.email_address),
        }

        result = jwt.encode(data, settings.SECRET_KEY)
        return result

    def make_authenticated_unsubscribe_url(self):
        return reverse(
            'unsubscribe-email',
            kwargs={'json_web_token': self.make_json_web_token()}
        )


class BlacklistedDomain(models.Model):
    domain = models.CharField(
        primary_key=True,
        max_length=200
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.domain
