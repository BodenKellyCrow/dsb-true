from django.contrib.auth import get_user_model, update_session_auth_hash
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project, Transaction, SocialPost, Conversation, Message, UserProfile
from .serializers import (
    ProjectSerializer, TransactionSerializer,
    UserProfileSerializer, PublicUserSerializer,
    SocialPostSerializer, CommentSerializer,
    ConversationSerializer, MessageSerializer,
)
from django.db.models import Q

User = get_user_model()

# -------------------
# USER PROFILE
# -------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user.profile, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserListView(generics.ListAPIView):
    queryset = UserProfile.objects.select_related("user").all()
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]


class UserProjectsView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(owner_id=self.kwargs["user_id"])


class UserFundedProjectsView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        funded_project_ids = Transaction.objects.filter(
            sender_id=self.kwargs["user_id"]
        ).values_list("project_id", flat=True)
        return Project.objects.filter(id__in=funded_project_ids)


class UserTransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))


# -------------------
# PASSWORD MANAGEMENT
# -------------------
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": "Both old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"error": "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # ✅ keeps session alive

        return Response({"status": "password changed successfully"}, status=status.HTTP_200_OK)


# -------------------
# PROJECTS & TRANSACTIONS
# -------------------
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related("owner")
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


# -------------------
# SOCIAL POSTS
# -------------------
class SocialPostListCreateView(generics.ListCreateAPIView):
    queryset = SocialPost.objects.all().select_related("author")
    serializer_class = SocialPostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FeedView(generics.ListAPIView):
    queryset = SocialPost.objects.all().select_related("author").order_by("-created_at")
    serializer_class = SocialPostSerializer
    permission_classes = [IsAuthenticated]


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = SocialPost.objects.get(id=post_id)
            if request.user in post.likes.all():
                post.likes.remove(request.user)
                return Response({"status": "unliked"})
            else:
                post.likes.add(request.user)
                return Response({"status": "liked"})
        except SocialPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


class AddCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = SocialPost.objects.get(id=post_id)
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user, post=post)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SocialPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


# -------------------
# MESSAGING
# -------------------
class UserConversationsView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class CreateConversationView(generics.CreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(conversation_id=self.kwargs["conversation_id"])

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, conversation_id=self.kwargs["conversation_id"])
