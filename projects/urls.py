from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TransactionViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
