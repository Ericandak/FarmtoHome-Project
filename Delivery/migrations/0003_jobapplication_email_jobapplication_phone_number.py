# Generated by Django 5.0.4 on 2024-10-16 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Delivery', '0002_jobapplication_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]