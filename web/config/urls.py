"""
URL configuration for AI Team Platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chat/', include('chat.urls')),
    path('api/users/', include('users.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)