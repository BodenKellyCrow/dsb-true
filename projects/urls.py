from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TransactionViewSet, UserProfileViewSet, UserProjectsView, UserFundedProjectsView, UserProfileUpdateView, SocialPostListCreateView, FeedView, LikePostView, AddCommentView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:user_id>/projects/', UserProjectsView.as_view(), name='user-projects'),
    path('users/<int:user_id>/funded/', UserFundedProjectsView.as_view(), name='user-funded-projects'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('social-posts/', SocialPostListCreateView.as_view(), name='social-posts'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('feed/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('feed/<int:post_id>/comment/', AddCommentView.as_view(), name='comment-post'),
]
