# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-09 13:17
from __future__ import unicode_literals

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    UserProfile = apps.get_model("users", "UserProfile")
    db_alias = schema_editor.connection.alias

    for profile in UserProfile.objects.using(db_alias).filter(
        user__is_staff=False,
        user__is_superuser=False,
        notify_product_updates=True,
    ):
        profile.notify_product_updates = False
        profile.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_add_new_feedback_settings'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
