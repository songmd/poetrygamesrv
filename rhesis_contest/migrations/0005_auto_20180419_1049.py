# Generated by Django 2.0.4 on 2018-04-19 02:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0004_auto_20180419_1048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='rhesis_contest.AppUser', verbose_name='用户'),
        ),
    ]