# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-03 11:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_auto_comparison_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportcomponent',
            name='coverage',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
