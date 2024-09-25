# Generated by Django 4.2.16 on 2024-09-20 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('role', models.CharField(choices=[('DEV', 'Developer'), ('TEST', 'Tester'), ('BA', 'Business Analyst'), ('MAN', 'Manager')], max_length=10)),
                ('department', models.CharField(choices=[('IT', 'IT')], max_length=10)),
                ('active_status', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
