# Generated by Django 3.1 on 2020-10-12 10:49

from django.conf import settings
import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0008_companytype'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyPaymentTerms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, unique=True, verbose_name='PaymentTerms Title')),
                ('deposit', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Deposit (in %)')),
                ('on_delivery', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Payment on delivery (in %)')),
                ('receiving', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Receiving (in %)')),
                ('remaining', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Remaining (in %)')),
                ('payment_days', models.PositiveIntegerField(verbose_name='Payment Days (in days)')),
                ('is_active', models.BooleanField(default=True)),
                ('extra_data', django.contrib.postgres.fields.hstore.HStoreField(blank=True, null=True)),
                ('create_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('update_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'PaymentTerms',
            },
        ),
    ]
