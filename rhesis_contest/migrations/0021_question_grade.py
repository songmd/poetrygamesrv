# Generated by Django 2.0.4 on 2018-05-05 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rhesis_contest', '0020_auto_20180505_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='grade',
            field=models.IntegerField(default=1, verbose_name='级别'),
        ),
    ]
