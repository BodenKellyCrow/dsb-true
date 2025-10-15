# projects/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
from .views import (
    RegisterView, UserListView, UserDetailView, UserDetailByIdView, ChangePasswordView,
    FollowToggleView, # Make sure this is present in views.py!
    ProjectListCreateView, ProjectDetailView, TransactionCreateView,
    SocialPostListCreateView, LikeCreateView, CommentCreateView,
    ConversationListCreateView, MessageListCreateView,
)

router = DefaultRouter()

urlpatterns = [
    # =============================
    # AUTH & USER MANAGEMENT
    # =============================
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/me/", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/", UserDetailByIdView.as_view(), name="user-detail-by-id"), 
    
    # ✅ FIX 1: Changed URL to match likely frontend request /api/users/<pk>/follow/
    path("users/<int:pk>/follow/", FollowToggleView.as_view(), name="user-follow-toggle"), 
    
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
    # ✅ FIX 2: Added 'chat/' prefix to match frontend request /api/chat/conversations/
    path("chat/conversations/", ConversationListCreateView.as_view(), name="conversations"),
    path("chat/conversations/<int:conversation_id>/messages/", MessageListCreateView.as_view(), name="messages"),
]