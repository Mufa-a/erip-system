from django.contrib import admin

from .models import EmailVerification


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "user",
        "verification_type",
        "status",
        "otp_attempts",
        "created_at",
        "expires_at",
        "verified_at",
    )
    list_filter = ("verification_type", "status")
    search_fields = ("email", "user__username", "user__email", "token")
    readonly_fields = ("token", "otp", "created_at", "verified_at")
    ordering = ("-created_at",)