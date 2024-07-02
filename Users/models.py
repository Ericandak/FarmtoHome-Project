from django.db import models
from django.contrib.auth.models import AbstractUser,Group,Permission
# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
       ('CUSTOMER', 'Customer'),
        ('SELLER', 'Seller'),
        ('DELIVERY', 'Delivery'),
        ('ADMIN','Admin'),
        ('MAIN','Main'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name='custom_user_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_permissions')


    def __str__(self):
        return self.username