# company/models.py
# ============================================================
# Added MpesaSettings model at the bottom.
# Uses django-cryptography to encrypt all sensitive credentials
# so even if the database is compromised, credentials are safe.
# ============================================================

from django.db import models
from django.utils import timezone
from accounts.models import User

# pip install django-cryptography
from cryptography.fernet import Fernet
from django.conf import settings
import base64


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
    plan_expires = models.DateTimeField(null=True, blank=True)
    max_users    = models.IntegerField(default=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Companies'

    @property
    def is_subscription_active(self):
        if self.plan_expires is None:
            return True
        return self.plan_expires >= timezone.now()

    @property
    def trial_minutes_left(self):
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
    has_accounting  = models.BooleanField(default=False)
    has_reports     = models.BooleanField(default=False)

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
    reference    = models.CharField(max_length=100, blank=True)
    notes        = models.TextField(blank=True)
    paid_at      = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.plan} - {self.status}"


# ============================================================
# Encryption helper
# Uses FIELD_ENCRYPTION_KEY from settings.py
# ============================================================

def _get_fernet():
    """Returns a Fernet instance using the FIELD_ENCRYPTION_KEY from settings."""
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
    if not key:
        raise ValueError(
            "FIELD_ENCRYPTION_KEY is not set in settings.py. "
            "Run: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and add it to your .env"
        )
    # Fernet key must be 32 url-safe base64-encoded bytes
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_field(value: str) -> str:
    """Encrypts a string value. Returns empty string if value is empty."""
    if not value:
        return ''
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    """Decrypts an encrypted string. Returns empty string if value is empty."""
    if not value:
        return ''
    try:
        f = _get_fernet()
        return f.decrypt(value.encode()).decode()
    except Exception:
        # If decryption fails (e.g. key changed), return empty
        return ''


# ============================================================
# MpesaSettings — one per company, all sensitive fields encrypted
# ============================================================

class MpesaSettings(models.Model):
    """
    Stores per-company M-Pesa Daraja API credentials.
    All sensitive fields are encrypted at rest using Fernet symmetric encryption.
    Even if the database is dumped, credentials cannot be read without FIELD_ENCRYPTION_KEY.
    """

    class Environment(models.TextChoices):
        SANDBOX    = 'sandbox',    'Sandbox (Testing)'
        PRODUCTION = 'production', 'Production (Live)'

    # One settings record per company
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='mpesa_settings'
    )

    # Environment: sandbox or production
    environment = models.CharField(
        max_length=20,
        choices=Environment.choices,
        default=Environment.SANDBOX
    )

    # Shortcode is not as sensitive but we store it plainly for display
    shortcode = models.CharField(
        max_length=20,
        blank=True,
        help_text="Your M-Pesa till or paybill number. e.g. 174379"
    )

    # All credential fields stored ENCRYPTED
    # We use TextField so encrypted strings (which are long) fit
    _consumer_key    = models.TextField(blank=True, db_column='consumer_key')
    _consumer_secret = models.TextField(blank=True, db_column='consumer_secret')
    _passkey         = models.TextField(blank=True, db_column='passkey')

    # Callback URL — not sensitive but must be set to Render URL in production
    callback_url = models.URLField(
        blank=True,
        help_text="e.g. https://erip-system.onrender.com/payments/mpesa-callback/"
    )

    # Whether M-Pesa is enabled for this company
    is_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Encrypted property accessors ──────────────────────────

    @property
    def consumer_key(self) -> str:
        """Returns the decrypted consumer key."""
        return decrypt_field(self._consumer_key)

    @consumer_key.setter
    def consumer_key(self, value: str):
        """Encrypts and stores the consumer key."""
        self._consumer_key = encrypt_field(value)

    @property
    def consumer_secret(self) -> str:
        """Returns the decrypted consumer secret."""
        return decrypt_field(self._consumer_secret)

    @consumer_secret.setter
    def consumer_secret(self, value: str):
        """Encrypts and stores the consumer secret."""
        self._consumer_secret = encrypt_field(value)

    @property
    def passkey(self) -> str:
        """Returns the decrypted passkey."""
        return decrypt_field(self._passkey)

    @passkey.setter
    def passkey(self, value: str):
        """Encrypts and stores the passkey."""
        self._passkey = encrypt_field(value)

    # ── Helper ────────────────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """Returns True only if all required credentials are present."""
        return bool(
            self.consumer_key and
            self.consumer_secret and
            self.shortcode and
            self.passkey and
            self.callback_url and
            self.is_enabled
        )

    def __str__(self):
        return f"M-Pesa Settings — {self.company.name} ({self.environment})"

    class Meta:
        verbose_name        = 'M-Pesa Settings'
        verbose_name_plural = 'M-Pesa Settings'