# Generated by Django 4.2.16 on 2024-09-23 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0005_alter_taskentries_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskentries',
            name='total_duration',
            field=models.DurationField(blank=True, null=True),
        ),
    ]
