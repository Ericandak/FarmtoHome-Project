# Generated by Django 5.0.4 on 2024-08-04 10:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0006_alter_user_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellerDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('FarmName', models.CharField(blank=True, max_length=15, null=True)),
                ('FarmAddress', models.CharField(blank=True, max_length=100, null=True)),
                ('Farmcity', models.CharField(blank=True, max_length=50, null=True)),
                ('Farmzip_code', models.CharField(blank=True, max_length=20, null=True)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Users.state')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
