from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from company.models import Company, CompanyUser
from verification.services import EmailVerificationService

User = get_user_model()


# =========================================================
# LOGIN VIEW
# =========================================================
def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        login_input = request.POST.get('username', '').strip()
        password    = request.POST.get('password')

        user = authenticate(request, username=login_input, password=password)

        if user is None:
            try:
                matched_user = User.objects.get(email=login_input)
                user = authenticate(
                    request,
                    username=matched_user.username,
                    password=password
                )
            except User.DoesNotExist:
                user = None

        if user is not None:

            # Block login if email not verified
            if not user.email_verified:
                messages.error(
                    request,
                    'Please verify your email before logging in. '
                    'Check your inbox for the verification code.'
                )
                return redirect('verification:verify_otp')

            login(
                request,
                user,
                backend='django.contrib.auth.backends.ModelBackend'
            )

            company_user = CompanyUser.objects.filter(
                user=user,
                is_active=True
            ).select_related('company').first()

            if company_user:
                request.session['company_id'] = company_user.company.id

            return redirect('dashboard')

        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'login.html')


# =========================================================
# LOGOUT VIEW
# =========================================================
def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')


# =========================================================
# USER REGISTRATION VIEW
# =========================================================
def register(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        email      = request.POST.get('email',      '').strip()
        password1  = request.POST.get('password1',  '')
        password2  = request.POST.get('password2',  '')
        plan       = request.POST.get('plan', 'starter')

        # Validation
        if not all([first_name, last_name, email, password1, password2]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'accounts/register.html', {'plan': plan})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html', {'plan': plan})

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/register.html', {'plan': plan})

        # Create user account
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        # Create company + start trial
        trial_expires = timezone.now() + timedelta(minutes=10)

        company_name = request.POST.get('company_name', '').strip()
        if not company_name:
            company_name = f"{first_name}'s Business"

        company = Company.objects.create(
            name=company_name,
            plan=Company.Plan.STARTER,
            plan_expires=trial_expires,
        )

        # Link user to company
        CompanyUser.objects.create(
            company=company,
            user=user,
            role=CompanyUser.Role.OWNER,
            is_active=True,
        )

        # Login user automatically
        login(
            request,
            user,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        request.session['company_id'] = company.id

        # Send email verification OTP
        try:
            EmailVerificationService.send_otp_verification(user)
            messages.success(
                request,
                f'Welcome to ERIP, {first_name}! '
                f'Your 10-minute trial has started. '
                f'Please verify your email — we sent a code to {email}.'
            )
        except Exception:
            messages.success(
                request,
                f'Welcome to ERIP, {first_name}! Your 10-minute trial has started.'
            )
            messages.warning(
                request,
                'We could not send a verification email. '
                'You can request one from your dashboard.'
            )

        return redirect('verification:verify_otp')

    plan = request.GET.get('plan', 'starter')
    return render(request, 'accounts/register.html', {'plan': plan})


# =========================================================
# USER LIST VIEW
# =========================================================
@login_required
def user_list(request):

    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('dashboard')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


# =========================================================
# ADD NEW USER
# =========================================================
@login_required
def user_add(request):

    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('dashboard')

    if request.method == 'POST':

        username   = request.POST.get('username')
        email      = request.POST.get('email')
        password   = request.POST.get('password')
        role       = request.POST.get('role')
        phone      = request.POST.get('phone')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/user_form.html', {'action': 'Add'})

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
        )

        messages.success(request, f'User {username} created successfully!')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Add',
        'roles': User.Role.choices,
    })


# =========================================================
# EDIT USER
# =========================================================
@login_required
def user_edit(request, pk):

    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('dashboard')

    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':

        user.email      = request.POST.get('email')
        user.role       = request.POST.get('role')
        user.phone      = request.POST.get('phone')
        user.first_name = request.POST.get('first_name')
        user.last_name  = request.POST.get('last_name')
        user.is_active  = request.POST.get('is_active') == 'on'

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f'User {user.username} updated!')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Edit',
        'edit_user': user,
        'roles': User.Role.choices,
    })


# =========================================================
# DELETE USER
# =========================================================
@login_required
def user_delete(request, pk):

    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('user_list')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('user_list')

    return render(request, 'accounts/user_confirm_delete.html', {
        'edit_user': user
    })


# =========================================================
# TOGGLE DARK/LIGHT THEME
# =========================================================
@login_required
def toggle_theme(request):

    if request.user.theme == 'dark':
        request.user.theme = 'light'
    else:
        request.user.theme = 'dark'

    request.user.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))