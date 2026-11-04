from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model supporting three roles:
    1. Admin - full system management
    2. Seller - manages their products and product orders
    3. Buyer - browses, manages cart, places orders
    """
    ROLE_ADMIN = 'admin'
    ROLE_SELLER = 'seller'
    ROLE_BUYER = 'buyer'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_SELLER, 'Seller'),
        (ROLE_BUYER, 'Buyer'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_BUYER,
        help_text="User role in the system: Admin, Seller, or Buyer"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser or self.is_staff

    @property
    def is_seller_role(self):
        return self.role == self.ROLE_SELLER

    @property
    def is_buyer_role(self):
        return self.role == self.ROLE_BUYER

    def save(self, *args, **kwargs):
        # Automatically grant staff permissions to admins for Django Admin access
        if self.role == self.ROLE_ADMIN or self.is_superuser:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
