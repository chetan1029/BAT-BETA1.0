# Generated by Django 3.1.1 on 2020-12-17 11:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0023_asset_assettransfer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='address1',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='address2',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='city',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='country',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='region',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='zip',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='address1',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='address2',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='city',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='country',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='region',
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='zip',
        ),
    ]
