# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-11-30 12:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_auto_20181124_0741'),
    ]

    operations = [
        migrations.AddField(
            model_name='goodschannel',
            name='aaa',
            field=models.IntegerField(default=0, max_length=10, verbose_name='项目'),
        ),
    ]
