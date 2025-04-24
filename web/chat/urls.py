from rest_framework_nested import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

conversations_router = routers.NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

app_name = 'chat'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]