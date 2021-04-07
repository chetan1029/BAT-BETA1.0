# Generated by Django 3.1.1 on 2021-02-01 08:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0028_auto_20210201_0811'),
        ('product', '0011_componentme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='componentgoldensample',
            name='componentme',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='golden_samples', to='product.componentme'),
        ),
        migrations.DeleteModel(
            name='ComponentMe',
        ),
    ]
