from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from .services import EmailVerificationService


# ------------------------------------------------------------------ #
#  Token-link verification (GET — user clicks the link in email)      #
# ------------------------------------------------------------------ #

class VerifyEmailTokenView(View):
    """Handles the link click from a token verification email."""

    def get(self, request, token):
        success, message, verification = EmailVerificationService.verify_token(token)

        if success:
            messages.success(request, message)
            return redirect("verification:success")  # adjust to your URL name
        else:
            messages.error(request, message)
            return redirect("verification:failed")   # adjust to your URL name


# ------------------------------------------------------------------ #
#  OTP flow (login required)                                          #
# ------------------------------------------------------------------ #

@method_decorator(login_required, name="dispatch")
class RequestOTPView(View):
    """Request a new OTP to be sent to the logged-in user's email."""

    def post(self, request):
        email = request.POST.get("email") or request.user.email
        EmailVerificationService.send_otp_verification(request.user, email=email)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": f"OTP sent to {email}."})

        messages.success(request, f"A verification code has been sent to {email}.")
        return redirect("verification:verify_otp")


@method_decorator(login_required, name="dispatch")
class VerifyOTPView(View):
    """Display the OTP entry form and handle OTP submission."""

    template_name = "verification/verify_otp.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        otp = request.POST.get("otp", "").strip()
        email = request.POST.get("email") or request.user.email

        if not otp:
            messages.error(request, "Please enter the OTP code.")
            return render(request, self.template_name)

        success, message, verification = EmailVerificationService.verify_otp(
            request.user, otp, email=email
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": success, "message": message})

        if success:
            messages.success(request, message)
            return redirect("verification:success")
        else:
            messages.error(request, message)
            return render(request, self.template_name)


# ------------------------------------------------------------------ #
#  Send token link (login required)                                   #
# ------------------------------------------------------------------ #

@method_decorator(login_required, name="dispatch")
class SendTokenVerificationView(View):
    """Send a token verification link to the logged-in user's email."""

    def post(self, request):
        email = request.POST.get("email") or request.user.email
        EmailVerificationService.send_token_verification(request.user, email=email)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": f"Verification link sent to {email}."})

        messages.success(request, f"A verification link has been sent to {email}.")
        return redirect("verification:verify_otp")


# ------------------------------------------------------------------ #
#  Simple result pages                                                #
# ------------------------------------------------------------------ #

def verification_success(request):
    return render(request, "verification/success.html")


def verification_failed(request):
    return render(request, "verification/failed.html")