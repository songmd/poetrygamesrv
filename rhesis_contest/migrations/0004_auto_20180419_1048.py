# Generated by Django 2.0.4 on 2018-04-19 02:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0003_auto_20180418_2325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rhesis_contest.AppUser', unique=True, verbose_name='用户'),
        ),
    ]
