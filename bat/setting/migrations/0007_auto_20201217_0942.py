# Generated by Django 3.1.1 on 2020-12-17 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0006_deliverytermname_deliveryterms_deliverytermservice'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deliverytermservice',
            options={'verbose_name_plural': 'Delivery Term Services'},
        ),
        migrations.AddField(
            model_name='deliverytermname',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
