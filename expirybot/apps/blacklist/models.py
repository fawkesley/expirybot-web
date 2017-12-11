from django.db import models


class BlacklistedEmailAddress(models.Model):
    email_address = models.EmailField(primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    unsubscribed = models.BooleanField(default=False)

    bounced = models.BooleanField(default=False)

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email_address


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
