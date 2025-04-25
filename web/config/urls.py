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
    path('', include('chat.urls')),  # Chat interface as main page
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)