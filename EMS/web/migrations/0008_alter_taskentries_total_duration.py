# Generated by Django 4.2.16 on 2024-09-24 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_alter_taskentries_total_duration_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskentries',
            name='total_duration',
            field=models.DurationField(blank=True, null=True),
        ),
    ]