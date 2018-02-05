# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-05 21:39
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0011_change_key_datetimes_to_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='pgpkey',
            name='capabilities',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('C', 'certifying other keys'), ('S', 'signing data'), ('E', 'encrypting data'), ('A', 'authenticating')], max_length=1), blank=True, default=[], size=None),
        ),
    ]
