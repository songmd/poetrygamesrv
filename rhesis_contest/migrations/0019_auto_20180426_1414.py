# Generated by Django 2.0.4 on 2018-04-26 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0018_auto_20180426_1022'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='fail',
            field=models.IntegerField(default=0, verbose_name='败局'),
        ),
        migrations.AddField(
            model_name='appuser',
            name='level',
            field=models.IntegerField(default=1, verbose_name='级别'),
        ),
        migrations.AddField(
            model_name='appuser',
            name='win',
            field=models.IntegerField(default=0, verbose_name='胜局'),
        ),
    ]
