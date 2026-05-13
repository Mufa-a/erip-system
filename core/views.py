from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# ─────────────────────────────────────────
#  LANDING PAGE  →  /
# ─────────────────────────────────────────
def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


# ─────────────────────────────────────────
#  DASHBOARD  →  /dashboard/
#  Only logged-in users can access this
# ─────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def dashboard(request):
    user = request.user

    # Block unverified users — redirect to OTP page
    if not user.email_verified:
        messages.warning(request, 'Please verify your email to access the dashboard.')
        return redirect('verification:verify_otp')

    context = {
        'user': user,
        'first_name': user.first_name or user.email,
    }
    return render(request, 'core/dashboard.html', context)


# ─────────────────────────────────────────
#  DEMO  →  /demo/
#  Anyone can view — no login required
# ─────────────────────────────────────────
def demo(request):
    return render(request, 'core/demo.html')


# ─────────────────────────────────────────
#  CONTACT  →  /contact/
# ─────────────────────────────────────────
def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        plan    = request.POST.get('plan', '')

        if not all([name, email, message]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'core/contact.html', {'plan': plan})

        # ── TODO: send email or save to DB here ──
        # For now we just show a success message
        messages.success(request, f"Thanks {name}! We'll be in touch within 24 hours.")
        return redirect('contact')

    plan = request.GET.get('plan', '')
    return render(request, 'core/contact.html', {'plan': plan})


# ─────────────────────────────────────────
#  STATIC PAGES
# ─────────────────────────────────────────
def privacy(request):
    return render(request, 'core/privacy.html')

def terms(request):
    return render(request, 'core/terms.html')

def support(request):
    return render(request, 'core/support.html')