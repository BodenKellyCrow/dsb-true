# projects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, UserDetailView, ChangePasswordView,
    ProjectListCreateView, TransactionCreateView,
    SocialPostListCreateView, LikeCreateView, CommentCreateView,
    ConversationListCreateView, MessageListCreateView,
)

router = DefaultRouter()
# You can add ViewSets here later if needed

urlpatterns = [
    # Auth & User
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("users/me/", UserDetailView.as_view(), name="user-detail"),
    path("users/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Projects + Transactions
    path("projects/", ProjectListCreateView.as_view(), name="projects"),
    path("transactions/", TransactionCreateView.as_view(), name="transactions"),

    # Social Posts
    path("social-posts/", SocialPostListCreateView.as_view(), name="social-posts"),
    path("social-posts/<int:post_id>/like/", LikeCreateView.as_view(), name="like-post"),
    path("social-posts/<int:post_id>/comment/", CommentCreateView.as_view(), name="add-comment"),

    # Messaging
    path("conversations/", ConversationListCreateView.as_view(), name="conversations"),
    path("conversations/<int:conversation_id>/messages/", MessageListCreateView.as_view(), name="messages"),
]
