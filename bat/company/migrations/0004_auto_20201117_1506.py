# Generated by Django 3.1.1 on 2020-11-17 15:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0003_auto_20201110_1018'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='companypaymentterms',
            unique_together={('company', 'title')},
        ),
    ]
