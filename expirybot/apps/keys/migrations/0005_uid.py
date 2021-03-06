# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-18 15:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0004_auto_20171218_1544'),
    ]

    operations = [
        migrations.CreateModel(
            name='UID',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uid_string', models.CharField(db_index=True, max_length=500)),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uids', to='keys.PGPKey')),
            ],
        ),
    ]
