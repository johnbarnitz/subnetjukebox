# Generated by Django 3.0.4 on 2020-03-16 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sj', '0004_auto_20200313_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='subnet',
            name='availcount',
            field=models.IntegerField(default=0),
        ),
    ]