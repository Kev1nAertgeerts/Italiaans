from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from apps.accounts.utils import UserAgentParser

User = get_user_model()


def login_user(request):
    template_name = "accounts/login.html"
    context = {}

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if User.objects.filter(username=username, is_active=False).exists():
            messages.error(request, "Account is inactief. Neem contact op met de beheerder.")
            return redirect(reverse("accounts:login_user"))
        else:
            user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            UserAgentParser().save_login_history(request)
            return redirect(reverse("core:home"))
        else:
            messages.error(request, "Invalid username or password")
            return redirect(reverse("accounts:login_user"))
    return render(request, template_name, context)


def logout_user(request):
    logout(request)
    return redirect(reverse("accounts:login_user"))