# Generated by Django 2.0.4 on 2018-04-19 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0010_auto_20180419_2318'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usershareinfo',
            old_name='user',
            new_name='from_user',
        ),
    ]