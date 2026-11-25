from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access as required by the spec:
    Super Admin, Company Owner, Accountant, Employee.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        COMPANY_OWNER = 'COMPANY_OWNER', 'Company Owner'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
        EMPLOYEE = 'EMPLOYEE', 'Employee'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COMPANY_OWNER)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_company_owner(self):
        return self.role == self.Role.COMPANY_OWNER

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE
