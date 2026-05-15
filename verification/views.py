from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .services import EmailVerificationService


class VerifyEmailTokenView(View):
    def get(self, request, token):
        success, message, verification = EmailVerificationService.verify_token(token)
        if success:
            messages.success(request, message)
            return redirect("verification:success")
        else:
            messages.error(request, message)
            return redirect("verification:failed")


@method_decorator(login_required, name="dispatch")
class RequestOTPView(View):
    def post(self, request):
        email = request.POST.get("email") or request.user.email
        EmailVerificationService.send_otp_verification(request.user, email=email)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": f"OTP sent to {email}."})
        messages.success(request, f"A verification code has been sent to {email}.")
        return redirect("verification:verify_otp")

class VerifyOTPView(View):
    template_name = "verification/verify_otp.html"

    def dispatch(self, request, *args, **kwargs):
        # Already verified — skip straight to dashboard
        if request.user.is_authenticated and request.user.email_verified:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        otp   = request.POST.get("otp", "").strip()
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

            # Log user in after verification
            from django.contrib.auth import login as auth_login
            auth_login(
                request,
                request.user,
                backend='django.contrib.auth.backends.ModelBackend'
            )

            # Set company session
            pending_company_id = request.session.get('pending_company_id')
            if pending_company_id:
                request.session['company_id'] = pending_company_id
                try:
                    del request.session['pending_company_id']
                    del request.session['pending_user_id']
                except KeyError:
                    pass

            return redirect("dashboard")
        else:
            messages.error(request, message)
            return render(request, self.template_name)


@method_decorator(login_required, name="dispatch")
class SendTokenVerificationView(View):
    def post(self, request):
        email = request.POST.get("email") or request.user.email
        EmailVerificationService.send_token_verification(request.user, email=email)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": f"Verification link sent to {email}."})
        messages.success(request, f"A verification link has been sent to {email}.")
        return redirect("verification:verify_otp")


def verification_success(request):
    return render(request, "verification/success.html")

def verification_failed(request):
    return render(request, "verification/failed.html")