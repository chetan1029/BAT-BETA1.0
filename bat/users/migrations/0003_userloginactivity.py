# Generated by Django 3.1.1 on 2020-12-02 09:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20201110_1018'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLoginActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP address')),
                ('logged_in_at', models.DateTimeField(auto_now=True, verbose_name='logged in date')),
                ('agent_info', models.CharField(blank=True, max_length=2096, null=True, verbose_name='Agent info')),
                ('location', models.CharField(blank=True, max_length=2096, null=True, verbose_name='location')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
