from django.urls import path

from . import views

app_name = "verification"

urlpatterns = [
    # Token-link verification (emailed link)
    path(
        "verify-email/token/<str:token>/",
        views.VerifyEmailTokenView.as_view(),
        name="verify_token",
    ),

    # OTP flow
    path(
        "verify-email/otp/request/",
        views.RequestOTPView.as_view(),
        name="request_otp",
    ),
    path(
        "verify-email/otp/",
        views.VerifyOTPView.as_view(),
        name="verify_otp",
    ),

    # Token link send (manual trigger)
    path(
        "verify-email/send-link/",
        views.SendTokenVerificationView.as_view(),
        name="send_token",
    ),

    # Result pages
    path("verify-email/success/", views.verification_success, name="success"),
    path("verify-email/failed/", views.verification_failed, name="failed"),
]