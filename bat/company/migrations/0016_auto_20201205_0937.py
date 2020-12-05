# Generated by Django 3.1.1 on 2020-12-05 09:37

from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0015_auto_20201202_1330'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='companyorderpaymentpaid',
            name='bank',
        ),
        migrations.AlterField(
            model_name='companyorderdeliveryproduct',
            name='companyorderdelivery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orderdeliveryproducts', to='company.companyorderdelivery'),
        ),
        migrations.AlterField(
            model_name='companyorderpayment',
            name='adjustment_amount',
            field=djmoney.models.fields.MoneyField(blank=True, decimal_places=2, default_currency='USD', max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='companyorderpayment',
            name='adjustment_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='companyorderpayment',
            name='adjustment_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
