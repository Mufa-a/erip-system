from django.db import models
from django.utils import timezone
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

    # ── Subscription fields ──
    plan         = models.CharField(max_length=20, choices=Plan.choices, default=Plan.STARTER)
    # ← Changed from DateField to DateTimeField so we can expire by minute not just day
    plan_expires = models.DateTimeField(null=True, blank=True)
    max_users    = models.IntegerField(default=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'

    @property
    def is_subscription_active(self):
        # If no expiry is set, allow access (grace period / admin-created company)
        if self.plan_expires is None:
            return True
        # Compare full datetime so 5-minute trials work correctly
        return self.plan_expires >= timezone.now()

    @property
    def trial_minutes_left(self):
        # Returns how many minutes remain in the trial (0 if expired)
        if self.plan_expires is None:
            return None
        delta = self.plan_expires - timezone.now()
        minutes = int(delta.total_seconds() / 60)
        return max(0, minutes)

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
    reference    = models.CharField(max_length=100, blank=True)  # M-Pesa/bank ref
    notes        = models.TextField(blank=True)
    paid_at      = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.plan} - {self.status}"