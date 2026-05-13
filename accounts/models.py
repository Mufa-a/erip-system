from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):    
    class Role(models.TextChoices):
        ADMIN      = 'admin',      'Admin'
        STAFF      = 'staff',      'Staff'
        ACCOUNTANT = 'accountant', 'Accountant'
        MANAGER    = 'manager',    'Manager'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', blank=True, null=True
    )
    theme = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    email_verified = models.BooleanField(default=False)  # ← NEW
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER