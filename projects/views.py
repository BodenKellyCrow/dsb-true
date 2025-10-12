# projects/views.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction, models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
# ⭐️ NOTE: Assuming you have a UserProfile model with a followers M2M field
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

# ... (RegisterView, UserListView, UserDetailView, ChangePasswordView remain the same) ...

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


# ⭐️ NEW VIEW: Follow/Unfollow Toggle
class FollowToggleView(APIView):
    """
    Follow or unfollow a user by ID.
    Endpoint: /users/<pk>/follow_toggle/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            # The user to be followed/unfollowed
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # You cannot follow yourself
        if target_user == request.user:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the current user's profile
        follower_profile = request.user.userprofile
        target_profile = target_user.userprofile

        # ⭐️ ASSUMPTION: UserProfile has a 'followers' M2M field
        # We check if the target's profile is being followed by the current user
        is_following = target_profile.followers.filter(id=request.user.id).exists()

        if is_following:
            # Unfollow logic (Remove the current user from the target's followers list)
            target_profile.followers.remove(request.user)
            message = f"Successfully unfollowed @{target_user.username}"
            action = "unfollowed"
        else:
            # Follow logic (Add the current user to the target's followers list)
            target_profile.followers.add(request.user)
            message = f"Successfully followed @{target_user.username}"
            action = "followed"

        # Return updated status and message
        return Response(
            {"message": message, "is_following": not is_following, "action": action}, 
            status=status.HTTP_200_OK
        )


# -------------------------------
# PROJECTS + TRANSACTIONS (Remainder of file remains the same)
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