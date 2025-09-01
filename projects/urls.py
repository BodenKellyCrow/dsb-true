from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TransactionViewSet, UserProfileViewSet, UserProjectsView, UserFundedProjectsView, UserProfileUpdateView, SocialPostListCreateView, FeedView, LikePostView, AddCommentView, UserTransactionHistoryView, PublicUserListView, UserConversationsView, CreateConversationView, MessageListCreateView
from django.http import HttpResponse
from django.core.management import call_command

def run_migrations(request):
    # Run Django migrations
    call_command('migrate')
    return HttpResponse("✅ Migrations applied successfully!")


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
    path('user-transactions/', UserTransactionHistoryView.as_view(), name='user-transactions'),
    path('users/', PublicUserListView.as_view(), name='public-users'),
    path('chat/conversations/', UserConversationsView.as_view(), name='chat-conversations'),
    path('chat/conversations/create/', CreateConversationView.as_view(), name='chat-create-convo'),
    path('chat/messages/<int:conversation_id>/', MessageListCreateView.as_view(), name='chat-messages'),
    path("run-migrations/", run_migrations),
]
