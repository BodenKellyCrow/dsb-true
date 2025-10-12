# projects/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
# ⭐️ NEW IMPORTS for JWT login/refresh
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
from .views import (
    RegisterView, UserListView, UserDetailView, UserDetailByIdView, ChangePasswordView,
    # Assuming you included FollowToggleView from the previous step:
    FollowToggleView, 
    ProjectListCreateView, ProjectDetailView, TransactionCreateView,
    SocialPostListCreateView, LikeCreateView, CommentCreateView,
    ConversationListCreateView, MessageListCreateView,
)

router = DefaultRouter()
# You can add ViewSets here later if needed

urlpatterns = [
    # =============================
    # AUTH & USER MANAGEMENT
    # =============================
    # ⭐️ LOGIN PATH (Matches frontend: '/auth/login/')
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    # ⭐️ TOKEN REFRESH PATH
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("users/", UserListView.as_view(), name="user-list"),  # Public user listing
    path("users/me/", UserDetailView.as_view(), name="user-detail"),  # Current user
    path("users/<int:pk>/", UserDetailByIdView.as_view(), name="user-detail-by-id"), 
    path("users/<int:pk>/follow_toggle/", FollowToggleView.as_view(), name="user-follow-toggle"), 
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
    path("conversations/", ConversationListCreateView.as_view(), name="conversations"),
    path("conversations/<int:conversation_id>/messages/", MessageListCreateView.as_view(), name="messages"),
]