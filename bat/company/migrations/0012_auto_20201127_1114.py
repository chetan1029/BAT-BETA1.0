# Generated by Django 3.1.1 on 2020-11-27 11:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0003_auto_20201110_1022'),
        ('company', '0011_auto_20201127_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyproduct',
            name='status',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.PROTECT, to='setting.status'),
        ),
        migrations.AddField(
            model_name='componentprice',
            name='status',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.PROTECT, to='setting.status'),
        ),
    ]
