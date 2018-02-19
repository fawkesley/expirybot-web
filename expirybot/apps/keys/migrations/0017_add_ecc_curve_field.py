# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-19 17:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0016_tweak_key_algorithm_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='pgpkey',
            name='ecc_curve',
            field=models.CharField(blank=True, choices=[('', 'Unknown'), ('ed25519', 'Ed25519 (sign only)'), ('cv25519', 'Curve25519 (encrypt only)'), ('nistp256', 'NIST P-256'), ('nistp384', 'NIST P-384'), ('nistp521', 'NIST P-521'), ('brainpoolP256r1', 'Brainpool P-256'), ('brainpoolP384r1', 'Brainpool P-384'), ('brainpoolP512r1', 'Brainpool P-512'), ('secp256k1', 'secp256k1 (sign only)')], default='', max_length=100),
        ),
        migrations.AddField(
            model_name='subkey',
            name='ecc_curve',
            field=models.CharField(blank=True, choices=[('', 'Unknown'), ('ed25519', 'Ed25519 (sign only)'), ('cv25519', 'Curve25519 (encrypt only)'), ('nistp256', 'NIST P-256'), ('nistp384', 'NIST P-384'), ('nistp521', 'NIST P-521'), ('brainpoolP256r1', 'Brainpool P-256'), ('brainpoolP384r1', 'Brainpool P-384'), ('brainpoolP512r1', 'Brainpool P-512'), ('secp256k1', 'secp256k1 (sign only)')], default='', max_length=100),
        ),
    ]
