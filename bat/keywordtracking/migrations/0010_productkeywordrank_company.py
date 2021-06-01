# Generated by Django 3.1.1 on 2021-05-26 08:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0029_auto_20210201_0811"),
        ("keywordtracking", "0009_remove_productkeywordrank_company"),
    ]

    operations = [
        migrations.AddField(
            model_name="productkeywordrank",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="company.company",
            ),
            preserve_default=False,
        )
    ]
