# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-19 17:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0020_brokenkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='brokenkey',
            name='error_message',
            field=models.TextField(blank=True, default=''),
        ),
    ]
