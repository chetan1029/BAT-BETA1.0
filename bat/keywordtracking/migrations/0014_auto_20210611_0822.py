# Generated by Django 3.1.1 on 2021-06-11 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keywordtracking', '0013_merge_20210607_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productkeywordrank',
            name='frequency',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
