# Generated by Django 4.2.16 on 2024-09-25 06:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0010_alter_taskentries_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='taskentries',
            unique_together=set(),
        ),
    ]