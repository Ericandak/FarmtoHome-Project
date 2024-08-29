from django.db import models
from django.contrib.auth.models import AbstractUser,Group,Permission
# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return self.name
class User(AbstractUser):
    role = models.ManyToManyField(Role)
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
class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}: {self.address}, {self.city}, {self.state}"

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set is_default=False for all other addresses of this user
            ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)
class SellerDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    FarmName=models.CharField(max_length=15, blank=True, null=True)
    FarmAddress=models.CharField(max_length=100, blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE) 
    Farmcity = models.CharField(max_length=50, null=True, blank=True)
    Farmzip_code = models.CharField(max_length=20, null=True, blank=True) 
    


