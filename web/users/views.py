from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, login, authenticate
from django.shortcuts import render, redirect
from django.views import View
from .serializers import UserSerializer

User = get_user_model()

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')  # Redirect to root which is now the chat list
        return render(request, 'users/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if not User.objects.filter(is_superuser=True).exists() or user.is_superuser:
                login(request, user)
                return redirect('/')  # Redirect to root which is now the chat list
            else:
                return render(request, 'users/login.html', {'error': 'Only superusers are allowed to login'})
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)