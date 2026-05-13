from django.utils import timezone

from .emails import send_otp_verification_email, send_token_verification_email
from .models import EmailVerification

MAX_OTP_ATTEMPTS = 5


class EmailVerificationService:
    """
    Service layer for all email verification operations.
    Handles token-link and OTP flows.
    """

    # ------------------------------------------------------------------ #
    #  Initiate verification                                               #
    # ------------------------------------------------------------------ #

    @classmethod
    def send_token_verification(cls, user, email=None):
        """
        Create a token-link verification record and dispatch the email.
        Invalidates any previous pending token verifications for this user/email.
        """
        email = email or user.email

        # Expire old pending token verifications
        EmailVerification.objects.filter(
            user=user,
            email=email,
            verification_type="token",
            status="pending",
        ).update(status="expired")

        verification = EmailVerification.objects.create(
            user=user,
            email=email,
            verification_type="token",
        )
        send_token_verification_email(user, verification)
        return verification

    @classmethod
    def send_otp_verification(cls, user, email=None):
        """
        Create an OTP verification record and dispatch the email.
        Invalidates any previous pending OTP verifications for this user/email.
        """
        email = email or user.email

        # Expire old pending OTP verifications
        EmailVerification.objects.filter(
            user=user,
            email=email,
            verification_type="otp",
            status="pending",
        ).update(status="expired")

        verification = EmailVerification.objects.create(
            user=user,
            email=email,
            verification_type="otp",
        )
        send_otp_verification_email(user, verification)
        return verification

    # ------------------------------------------------------------------ #
    #  Confirm / validate                                                  #
    # ------------------------------------------------------------------ #

    @classmethod
    def verify_token(cls, token: str):
        """
        Validate a token-link click.

        Returns:
            (success: bool, message: str, verification: EmailVerification | None)
        """
        try:
            verification = EmailVerification.objects.get(
                token=token,
                verification_type="token",
            )
        except EmailVerification.DoesNotExist:
            return False, "Invalid verification link.", None

        if verification.is_verified:
            return False, "This link has already been used.", verification

        if verification.is_expired or verification.status == "expired":
            verification.mark_expired()
            return False, "This verification link has expired. Please request a new one.", verification

        # All good — mark verified
        verification.mark_verified()
        cls._mark_user_email_verified(verification)
        return True, "Email verified successfully.", verification

    @classmethod
    def verify_otp(cls, user, otp: str, email=None):
        """
        Validate an OTP code submitted by the user.

        Returns:
            (success: bool, message: str, verification: EmailVerification | None)
        """
        email = email or user.email

        try:
            verification = EmailVerification.objects.get(
                user=user,
                email=email,
                verification_type="otp",
                status="pending",
            )
        except EmailVerification.DoesNotExist:
            return False, "No active OTP found. Please request a new code.", None

        if verification.is_expired:
            verification.mark_expired()
            return False, "Your OTP has expired. Please request a new one.", verification

        if verification.otp_attempts >= MAX_OTP_ATTEMPTS:
            verification.mark_expired()
            return False, "Too many incorrect attempts. Please request a new code.", verification

        if verification.otp != otp.strip():
            verification.otp_attempts += 1
            verification.save(update_fields=["otp_attempts"])
            remaining = MAX_OTP_ATTEMPTS - verification.otp_attempts
            return False, f"Incorrect OTP. {remaining} attempt(s) remaining.", verification

        # Correct OTP
        verification.mark_verified()
        cls._mark_user_email_verified(verification)
        return True, "Email verified successfully.", verification

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _mark_user_email_verified(verification):
        """
        Mark the user's email_verified flag if the model supports it.
        Adjust field name to match your User model.
        """
        user = verification.user
        if hasattr(user, "email_verified"):
            user.email_verified = True
            user.save(update_fields=["email_verified"])

    @staticmethod
    def get_pending_otp(user, email=None):
        """Return the active (pending, non-expired) OTP record for a user, if any."""
        email = email or user.email
        return EmailVerification.objects.filter(
            user=user,
            email=email,
            verification_type="otp",
            status="pending",
            expires_at__gt=timezone.now(),
        ).first()