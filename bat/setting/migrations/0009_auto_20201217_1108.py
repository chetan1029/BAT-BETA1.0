# Generated by Django 3.1.1 on 2020-12-17 11:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0008_auto_20201217_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliveryterms',
            name='deliverytermname',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deliveryterms', to='setting.deliverytermname'),
        ),
    ]
