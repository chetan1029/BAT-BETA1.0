# Generated by Django 3.1.1 on 2021-05-14 11:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0012_auto_20210122_1602'),
        ('keywordtracking', '0003_auto_20210511_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productkeyword',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='setting.status'),
        ),
    ]
