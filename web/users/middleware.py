from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class SuperuserAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for login page and static files
        if request.path.startswith('/static/') or request.path == reverse('users:login'):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('users:login')

        # Check if any superuser exists
        if not User.objects.filter(is_superuser=True).exists():
            # Allow access if no superuser exists yet
            return self.get_response(request)

        # If user is not a superuser, redirect to login
        if not request.user.is_superuser:
            return redirect('users:login')

        return self.get_response(request)