# Generated by Django 3.1.1 on 2020-12-11 08:52

import django.contrib.postgres.fields.hstore
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0004_category_is_vendor_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, null=True),
        ),
    ]
