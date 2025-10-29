# projects/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, UserListView, UserDetailView, UserDetailByIdView, ChangePasswordView,
    ProjectListCreateView, ProjectDetailView, TransactionCreateView,
    SocialPostListCreateView, LikeCreateView, CommentCreateView,
    ConversationListCreateView, MessageListCreateView, FollowToggleView
)

router = DefaultRouter()

urlpatterns = [
    # =============================
    # AUTH & USER MANAGEMENT
    # =============================
    path("auth/register/", RegisterView.as_view(), name="register"),
    # This route is specifically for the currently logged-in user's editable profile
    path("auth/user/", UserDetailView.as_view(), name="user-detail"), # ✅ Renamed to /auth/user/ to match frontend call in Profile.jsx
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailByIdView.as_view(), name="user-detail-by-id"),
    path("users/<int:pk>/follow/", FollowToggleView.as_view(), name="follow-toggle"), 
    path("users/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # =============================
    # PROJECTS & TRANSACTIONS
    # =============================
    path("projects/", ProjectListCreateView.as_view(), name="projects"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("transactions/", TransactionCreateView.as_view(), name="transactions"),

    # =============================
    # SOCIAL POSTS & ENGAGEMENT
    # =============================
    path("social-posts/", SocialPostListCreateView.as_view(), name="social-posts"),
    path("social-posts/<int:post_id>/like/", LikeCreateView.as_view(), name="like-post"),
    path("social-posts/<int:post_id>/comment/", CommentCreateView.as_view(), name="add-comment"),

    # =============================
    # MESSAGING 
    # =============================
    # ✅ FIX: Match URL endpoint to the MessageListCreateView logic from views.py
    path("conversations/", ConversationListCreateView.as_view(), name="conversations"),
    path("conversations/<int:conversation_id>/messages/", MessageListCreateView.as_view(), name="messages"),
]