"""
URL configuration for AI Team Platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chat/', include('web.chat.urls')),
    path('api/users/', include('web.users.urls')),
    path('', include('web.users.urls')),  # Include user URLs at root for auth views
    path('', include('web.chat.urls')),  # Chat interface as main page
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)