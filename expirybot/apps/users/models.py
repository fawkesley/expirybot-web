from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# from expirybot.apps.blacklist.models import EmailAddress


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    notify_email_addresses = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def claimed_email_addresses(self):
        return []


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)

# class EmailAddressOwnershipProof(models.Model):
#     email_address = models.OneToOneField(EmailAddress, null=True)
