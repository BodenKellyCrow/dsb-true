# projects/views.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction, models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Project, Transaction, UserProfile,
    SocialPost, Like, Comment, Conversation, Message
)
from .serializers import (
    UserSerializer, ProjectSerializer, TransactionSerializer,
    UserProfileSerializer, SocialPostSerializer, LikeSerializer,
    CommentSerializer, ConversationSerializer, MessageSerializer
)


# -------------------------------
# AUTH / USER MANAGEMENT
# -------------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data["username"])

        # Ensure UserProfile exists (failsafe)
        UserProfile.objects.get_or_create(user=user)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": response.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserListView(generics.ListAPIView):
    """
    Public user list endpoint used by the frontend Explore page.
    Returns users with profile fields (profile_image, bio) available via serializer.
    """
    queryset = User.objects.all().select_related('userprofile')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(APIView):
    """
    Get or update the currently authenticated user's details.
    Used for /auth/user/ endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Update username only."""
        user = request.user
        new_username = request.data.get("username")

        if new_username:
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                return Response(
                    {"error": "Username already taken."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.username = new_username
            user.save()

        return Response(UserSerializer(user).data)


class UserDetailByIdView(generics.RetrieveAPIView):
    """
    Get a single user's details by ID (for viewing other users' profiles).
    Used for /users/<id>/ endpoint.
    """
    queryset = User.objects.all().select_related('userprofile')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"success": "Password updated successfully."})


# -------------------------------
# PROJECTS + TRANSACTIONS
# -------------------------------

class ProjectListCreateView(generics.ListCreateAPIView):
    """
    List all projects or create a new project.
    Supports filtering by owner: /projects/?owner=<user_id>
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Project.objects.all().select_related('owner__userprofile').order_by("-created_at")
        owner_id = self.request.query_params.get('owner', None)
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectDetailView(generics.RetrieveAPIView):
    """
    Get a single project's details by ID.
    Used for /projects/<id>/ endpoint.
    """
    queryset = Project.objects.all().select_related('owner__userprofile')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]


class TransactionCreateView(generics.CreateAPIView):
    """
    Create a new transaction (fund a project).
    Requires: receiver (user_id), project (project_id), amount
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.validated_data["receiver"]
        project = serializer.validated_data["project"]
        amount = serializer.validated_data["amount"]

        with transaction.atomic():
            sender_profile = sender.userprofile
            receiver_profile = receiver.userprofile

            if sender_profile.balance < amount:
                raise ValidationError("Insufficient balance.")

            sender_profile.balance -= amount
            receiver_profile.balance += amount
            project.current_funding += amount

            sender_profile.save()
            receiver_profile.save()
            project.save()

            serializer.save(sender=sender)


# -------------------------------
# SOCIAL POSTS + ENGAGEMENT
# -------------------------------

class SocialPostListCreateView(generics.ListCreateAPIView):
    """
    List all social posts or create a new post.
    Supports filtering by author: /social-posts/?author=<user_id>
    """
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = SocialPost.objects.all().select_related('author__userprofile').order_by("-created_at")
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class LikeCreateView(generics.CreateAPIView):
    """
    Create a like on a post.
    Requires: post (post_id)
    """
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentCreateView(generics.CreateAPIView):
    """
    Create a comment on a post.
    Requires: post (post_id), content
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -------------------------------
# CHAT / MESSAGING
# -------------------------------

class ConversationListCreateView(generics.ListCreateAPIView):
    """
    List all conversations for the authenticated user or create a new conversation.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            models.Q(user1=self.request.user) | models.Q(user2=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(user1=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    """
    List all messages in a conversation or send a new message.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        return Message.objects.filter(conversation_id=conversation_id).order_by("timestamp")

    def perform_create(self, serializer):
        conversation_id = self.kwargs["conversation_id"]
        serializer.save(sender=self.request.user, conversation_id=conversation_id)