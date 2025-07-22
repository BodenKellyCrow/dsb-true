from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TransactionViewSet, UserProfileViewSet, UserProjectsView, UserFundedProjectsView, UserProfileUpdateView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:user_id>/projects/', UserProjectsView.as_view(), name='user-projects'),
    path('users/<int:user_id>/funded/', UserFundedProjectsView.as_view(), name='user-funded-projects'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
]
