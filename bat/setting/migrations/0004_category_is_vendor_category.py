# Generated by Django 3.1.1 on 2020-12-08 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0003_auto_20201110_1022'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_vendor_category',
            field=models.BooleanField(default=False, verbose_name='Is Vendor Category?'),
        ),
    ]
