# Generated by Django 3.1.1 on 2021-03-01 10:26

import bat.market.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0002_auto_20210301_1013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amazonmarketplace',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=bat.market.models.file_name, verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='amazonmarketplace',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Name'),
        ),
    ]
