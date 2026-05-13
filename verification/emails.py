from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_token_verification_email(user, verification):
    """Send a clickable token verification link to the user's email."""
    verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email/token/{verification.token}/"

    context = {
        "user": user,
        "verify_url": verify_url,
        "expiry_hours": 24,
    }

    # Render HTML email (optional — falls back to plain text if template missing)
    try:
        html_message = render_to_string("verification/email_token.html", context)
        plain_message = strip_tags(html_message)
    except Exception:
        plain_message = (
            f"Hi {user.get_full_name() or user.username},\n\n"
            f"Please verify your email by clicking the link below:\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"— The Erip Team"
        )
        html_message = None

    send_mail(
        subject="Verify your Erip email address",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[verification.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_otp_verification_email(user, verification):
    """Send a 6-digit OTP code to the user's email."""
    context = {
        "user": user,
        "otp": verification.otp,
        "expiry_minutes": 10,
    }

    try:
        html_message = render_to_string("verification/email_otp.html", context)
        plain_message = strip_tags(html_message)
    except Exception:
        plain_message = (
            f"Hi {user.get_full_name() or user.username},\n\n"
            f"Your Erip verification code is: {verification.otp}\n\n"
            f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
            f"— The Erip Team"
        )
        html_message = None

    send_mail(
        subject="Your Erip verification code",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[verification.email],
        html_message=html_message,
        fail_silently=False,
    )