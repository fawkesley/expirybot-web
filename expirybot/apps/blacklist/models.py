import uuid

from django.db import models


class ExampleModel(models.Model):

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
