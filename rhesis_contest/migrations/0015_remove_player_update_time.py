# Generated by Django 2.0.4 on 2018-04-20 07:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0014_auto_20180420_1145'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='update_time',
        ),
    ]
