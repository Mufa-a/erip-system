from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            request.session.flush()  # ✅ clears old company_id
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')


@login_required
def user_list(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


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
            last_name=last_name
        )
        messages.success(request, f'User {username} created successfully!')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Add',
        'roles': User.Role.choices
    })


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
        new_password    = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
        user.save()
        messages.success(request, f'User {user.username} updated!')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Edit',
        'edit_user': user,
        'roles': User.Role.choices
    })


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
    return render(request, 'accounts/user_confirm_delete.html', {'edit_user': user})


@login_required
def toggle_theme(request):
    if request.user.theme == 'dark':
        request.user.theme = 'light'
    else:
        request.user.theme = 'dark'
    request.user.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))