# Generated by Django 3.1.1 on 2020-12-21 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0005_category_extra_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_sales_channel_category',
            field=models.BooleanField(default=False, verbose_name='Is Sales Channel Category?'),
        ),
    ]
