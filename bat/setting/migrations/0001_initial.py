# Generated by Django 3.1.1 on 2020-11-09 16:25

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Category Name')),
                ('rule', models.CharField(blank=True, max_length=50, null=True, verbose_name='Category Rule')),
                ('is_active', models.BooleanField(default=True)),
                ('create_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('update_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PaymentTerms',
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
            ],
            options={
                'verbose_name_plural': 'PaymentTerms',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Status Name')),
                ('is_active', models.BooleanField(default=True)),
                ('create_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('update_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='setting.status')),
            ],
            options={
                'verbose_name_plural': 'Statuses',
                'ordering': ['name'],
            },
        ),
    ]
