# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='collected_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
