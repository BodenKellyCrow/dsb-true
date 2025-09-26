from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, TransactionViewSet,
    UserProjectsView, UserFundedProjectsView,
    SocialPostListCreateView, FeedView, LikePostView, AddCommentView,
    UserTransactionHistoryView, PublicUserListView,
    UserConversationsView, CreateConversationView, MessageListCreateView,
    MeView
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),

    # Profile / User endpoints
    path('me/', MeView.as_view(), name='me'),
    path('users/<int:user_id>/projects/', UserProjectsView.as_view(), name='user-projects'),
    path('users/<int:user_id>/funded/', UserFundedProjectsView.as_view(), name='user-funded-projects'),
    path('users/', PublicUserListView.as_view(), name='public-users'),

    # Social feed
    path('social-posts/', SocialPostListCreateView.as_view(), name='social-posts'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('feed/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('feed/<int:post_id>/comment/', AddCommentView.as_view(), name='comment-post'),

    # Transactions
    path('user-transactions/', UserTransactionHistoryView.as_view(), name='user-transactions'),

    # Chat / Messaging
    path('chat/conversations/', UserConversationsView.as_view(), name='chat-conversations'),
    path('chat/conversations/create/', CreateConversationView.as_view(), name='chat-create-convo'),
    path('chat/messages/<int:conversation_id>/', MessageListCreateView.as_view(), name='chat-messages'),
]
