# Generated by Django 2.0.4 on 2018-04-19 03:53

from django.db import migrations, models
import rhesis_contest.models


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0006_auto_20180419_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appuser',
            name='id',
            field=models.CharField(default=rhesis_contest.models.uuid_char, max_length=128, primary_key=True, serialize=False, verbose_name='用户标识'),
        ),
    ]
