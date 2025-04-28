from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListView.as_view(), name='list'),
    path('room/', views.ChatRoomView.as_view(), name='chat_room'),
    path('room/<int:pk>/', views.ChatRoomView.as_view(), name='chat_room'),
    path('api/', include(router.urls)),
]