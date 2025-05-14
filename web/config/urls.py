"""
URL configuration for AI Team Platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # API routes
    path('api/chat/', include('web.chat.urls', namespace='chat_api')),
    path('api/users/', include('web.users.urls', namespace='users_api')),
    # Auth routes
    path('auth/', include('web.users.urls')),  # Move auth routes under /auth/
    # Main app routes - chat as the main interface
    path('', include('web.chat.urls')),  # Chat interface as main page
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)