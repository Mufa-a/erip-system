import random
import string
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


def generate_otp():
    """Generate a 6-digit OTP."""
    return "".join(random.choices(string.digits, k=6))


def generate_token():
    """Generate a secure UUID token."""
    return str(uuid.uuid4())


class EmailVerification(models.Model):
    VERIFICATION_TYPE_CHOICES = [
        ("token", "Token Link"),
        ("otp", "OTP Code"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )
    email = models.EmailField()
    verification_type = models.CharField(
        max_length=10,
        choices=VERIFICATION_TYPE_CHOICES,
    )
    token = models.CharField(max_length=255, unique=True, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    otp_attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"

    def __str__(self):
        return f"{self.email} - {self.verification_type} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-generate token or OTP based on type
        if self.verification_type == "token" and not self.token:
            self.token = generate_token()
        elif self.verification_type == "otp" and not self.otp:
            self.otp = generate_otp()

        # Set expiry: 24 hrs for token, 10 mins for OTP
        if not self.expires_at:
            if self.verification_type == "token":
                self.expires_at = timezone.now() + timedelta(hours=24)
            else:
                self.expires_at = timezone.now() + timedelta(minutes=10)

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_verified(self):
        return self.status == "verified"

    def mark_verified(self):
        self.status = "verified"
        self.verified_at = timezone.now()
        self.save(update_fields=["status", "verified_at"])

    def mark_expired(self):
        self.status = "expired"
        self.save(update_fields=["status"])