# projects/views.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction, models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import logging

# ✅ Add logging
logger = logging.getLogger(__name__)

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
        try:
            response = super().create(request, *args, **kwargs)
            user = User.objects.get(username=response.data["username"])

            # Ensure UserProfile exists
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
        except Exception as e:
            logger.error(f"❌ Registration error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserListView(generics.ListAPIView):
    """
    Public user list endpoint used by the frontend Explore page.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return User.objects.all().select_related('userprofile')

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ UserListView error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """Get or update the currently authenticated user's details."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"❌ UserDetailView GET error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """Partial update of user profile"""
        try:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"❌ UserDetailView PATCH error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# projects/views.py

# ... (around line 105)

class UserDetailByIdView(generics.RetrieveAPIView):
    """Get a single user's details by ID"""
    queryset = User.objects.all().select_related('userprofile')
    # ❌ OLD: serializer_class = UserSerializer
    # ✅ FIX: Use the public serializer for public views
    serializer_class = PublicUserSerializer 
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ UserDetailByIdView error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ...


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
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
        except Exception as e:
            logger.error(f"❌ ChangePasswordView error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------------
# PROJECTS + TRANSACTIONS
# -------------------------------

class ProjectListCreateView(generics.ListCreateAPIView):
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
    queryset = Project.objects.all().select_related('owner__userprofile')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]


class TransactionCreateView(generics.CreateAPIView):
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
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = SocialPost.objects.all().select_related('author__userprofile').order_by("-created_at")
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(author=self.request.user)
        except Exception as e:
            logger.error(f"❌ SocialPost create error: {str(e)}")
            raise


class LikeCreateView(generics.CreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -------------------------------
# CHAT / MESSAGING
# -------------------------------

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            models.Q(user1=self.request.user) | models.Q(user2=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(user1=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        return Message.objects.filter(conversation_id=conversation_id).order_by("timestamp")

    def perform_create(self, serializer):
        conversation_id = self.kwargs["conversation_id"]
        serializer.save(sender=self.request.user, conversation_id=conversation_id)

# projects/views.py (Ensure this class is present and correctly indented)
# ...

# projects/views.py

# ... (inside the class definition) ...

class FollowToggleView(APIView):
    """
    Follow or unfollow a user by ID.
    Endpoint: /users/<pk>/follow_toggle/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            # 1. Retrieve the user being targeted (to follow/unfollow)
            target_user = User.objects.select_related('userprofile').get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Prevent self-following
        if target_user == request.user:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Get the target user's profile to access the 'followers' M2M field
        target_profile = target_user.userprofile

        # 4. Check the current following status
        # We check if the current user (request.user) is in the target user's followers list.
        is_following = target_profile.followers.filter(id=request.user.id).exists()

        if is_following:
            # 5. UNFOLLOW action: Remove the current user from the target's followers list
            target_profile.followers.remove(request.user)
            message = f"Successfully unfollowed @{target_user.username}"
            action = "unfollowed"
        else:
            # 5. FOLLOW action: Add the current user to the target's followers list
            target_profile.followers.add(request.user)
            message = f"Successfully followed @{target_user.username}"
            action = "followed"

        # 6. Return the updated status and a success message
        return Response(
            {
                "message": message, 
                "is_following": not is_following, # The new status
                "action": action
            }, 
            status=status.HTTP_200_OK
        )