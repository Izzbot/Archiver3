# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='URL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('init_url', models.CharField(max_length=1000)),
                ('final_url', models.CharField(max_length=1000)),
                ('status', models.CharField(max_length=4)),
                ('title', models.CharField(max_length=500)),
            ],
        ),
    ]
