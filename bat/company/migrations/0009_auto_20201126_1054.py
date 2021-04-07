# Generated by Django 3.1.1 on 2020-11-26 10:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("setting", "0003_auto_20201110_1022"),
        ("company", "0008_auto_20201126_0911"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="componentgoldensample", name="componentme"
        ),
        migrations.AddField(
            model_name="componentgoldensample",
            name="company",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="company.company",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="companytype",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="companytype_category",
                to="setting.category",
            ),
        ),
    ]
