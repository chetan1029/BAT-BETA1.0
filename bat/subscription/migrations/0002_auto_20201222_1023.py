# Generated by Django 3.1.1 on 2020-12-22 10:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0026_merge_20201221_0744'),
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='member',
        ),
        migrations.AddField(
            model_name='subscription',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='company.company'),
            preserve_default=False,
        ),
    ]
