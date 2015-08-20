# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0003_auto_20150806_1922'),
    ]

    operations = [
        migrations.RenameField(
            model_name='url',
            old_name='wback_url',
            new_name='snapshot_url',
        ),
        migrations.RemoveField(
            model_name='url',
            name='wback_date',
        ),
    ]
