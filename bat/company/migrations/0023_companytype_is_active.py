# Generated by Django 3.1.1 on 2020-12-19 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0022_merge_20201217_1223'),
    ]

    operations = [
        migrations.AddField(
            model_name='companytype',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
