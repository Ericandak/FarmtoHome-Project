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

class State(models.Model):
    name = models.CharField(max_length=50)  # State name
    country = models.CharField(max_length=100)  # Country name

    def __str__(self):
        return f"{self.name}, {self.country}"
class Address_table(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Foreign key to User model
    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)  # Adjust the length as needed
    state = models.ForeignKey(State, on_delete=models.CASCADE)  # Foreign key to State model

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}"
