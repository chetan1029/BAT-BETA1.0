# Generated by Django 3.1.1 on 2021-01-02 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20201222_0351'),
    ]

    operations = [
        migrations.AddField(
            model_name='productparent',
            name='model_number',
            field=models.CharField(blank=True, max_length=200, verbose_name='Model Number'),
        ),
    ]
