from django.db import models
from accounts.models import User


class Company(models.Model):
    class Plan(models.TextChoices):
        STARTER    = 'starter',    'Starter'
        BUSINESS   = 'business',   'Business'
        ENTERPRISE = 'enterprise', 'Enterprise'

    name         = models.CharField(max_length=200)
    email        = models.EmailField(blank=True)
    phone        = models.CharField(max_length=20, blank=True)
    address      = models.TextField(blank=True)
    city         = models.CharField(max_length=100, blank=True)
    country      = models.CharField(max_length=100, default='Kenya')
    tax_number   = models.CharField(max_length=50, blank=True)
    logo         = models.ImageField(upload_to='logos/', blank=True, null=True)
    currency     = models.CharField(max_length=10, default='KES')
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    # Subscription fields
    plan         = models.CharField(max_length=20, choices=Plan.choices, default=Plan.STARTER)
    plan_expires = models.DateField(null=True, blank=True)
    max_users    = models.IntegerField(default=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'

    @property
    def is_subscription_active(self):
        from django.utils import timezone
        if self.plan_expires is None:
            return True  # no expiry set yet (grace period)
        return self.plan_expires >= timezone.now().date()

    @property
    def user_count(self):
        return self.members.filter(is_active=True).count()

    @property
    def can_add_user(self):
        return self.user_count < self.max_users


class CompanyUser(models.Model):
    class Role(models.TextChoices):
        OWNER      = 'owner',      'Owner'
        ADMIN      = 'admin',      'Admin'
        MANAGER    = 'manager',    'Manager'
        ACCOUNTANT = 'accountant', 'Accountant'
        STAFF      = 'staff',      'Staff'

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f"{self.user.username} @ {self.company.name}"


class CompanySettings(models.Model):
    company         = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    has_hr          = models.BooleanField(default=True)
    has_inventory   = models.BooleanField(default=True)
    has_suppliers   = models.BooleanField(default=True)
    has_accounting  = models.BooleanField(default=False)  # business+ only
    has_reports     = models.BooleanField(default=False)  # business+ only

    def __str__(self):
        return f"Settings for {self.company.name}"


class SubscriptionPayment(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        PAID     = 'paid',     'Paid'
        FAILED   = 'failed',   'Failed'

    company      = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscription_payments')
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    plan         = models.CharField(max_length=20, choices=Company.Plan.choices)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    months_paid  = models.IntegerField(default=1)
    reference    = models.CharField(max_length=100, blank=True)  # Mpesa/bank ref
    notes        = models.TextField(blank=True)
    paid_at      = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.plan} - {self.status}"