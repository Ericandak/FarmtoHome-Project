# Generated by Django 5.0.4 on 2024-08-04 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0007_sellerdetails'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ManyToManyField(to='Users.role'),
        ),
    ]
