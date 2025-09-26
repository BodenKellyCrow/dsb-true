from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, TransactionViewSet,
    MeView, PublicUserListView, UserProjectsView,
    UserFundedProjectsView, UserTransactionHistoryView,
    SocialPostListCreateView, FeedView, LikePostView, AddCommentView,
    UserConversationsView, CreateConversationView, MessageListCreateView,
    ChangePasswordView,  # ✅ NEW
)

# Routers for DRF ViewSets
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    # DRF router URLs
    path('', include(router.urls)),

    # User profile
    path('me/', MeView.as_view(), name='me'),  # GET/PUT/PATCH for logged-in user
    path('me/change-password/', ChangePasswordView.as_view(), name='change-password'),  # ✅ NEW
    path('users/', PublicUserListView.as_view(), name='public-users'),
    path('users/<int:user_id>/projects/', UserProjectsView.as_view(), name='user-projects'),
    path('users/<int:user_id>/funded-projects/', UserFundedProjectsView.as_view(), name='user-funded-projects'),
    path('users/transactions/', UserTransactionHistoryView.as_view(), name='user-transactions'),

    # Social posts
    path('social-posts/', SocialPostListCreateView.as_view(), name='social-posts'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('social-posts/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('social-posts/<int:post_id>/comment/', AddCommentView.as_view(), name='add-comment'),

    # Messaging
    path('conversations/', UserConversationsView.as_view(), name='user-conversations'),
    path('conversations/create/', CreateConversationView.as_view(), name='create-conversation'),
    path('conversations/<int:conversation_id>/messages/', MessageListCreateView.as_view(), name='conversation-messages'),
]
