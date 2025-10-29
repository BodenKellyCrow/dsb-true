# projects/views.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction, models
from rest_framework import generics, permissions, status
# ✅ ADDED: MultiPartParser to handle file uploads (profile_image)
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import logging

# ✅ Add logging
logger = logging.getLogger(__name__)

from .models import (
    Project, Transaction, UserProfile,
    SocialPost, Conversation, Message
)
from .serializers import (
    UserSerializer, ProjectSerializer, TransactionSerializer,
    SocialPostSerializer, LikeSerializer,
    CommentSerializer, ConversationSerializer, MessageSerializer, PublicUserSerializer
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
    # ✅ FIX: Use PublicUserSerializer for public lists
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # We need to select_related('userprofile') for the serializer fields (bio, profile_image)
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
    # ✅ FIX 1: Add parsers to correctly handle profile image file uploads (multipart/form-data)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"❌ UserDetailView GET error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """Partial update of user profile, including file upload (image)"""
        try:
            # The serializer handles validation and saving User and UserProfile fields
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            
            # ✅ FIX 2: Ensure the user's current password is NOT required for profile updates
            # The serializer update method in projects/serializers.py now handles complex fields
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"❌ UserDetailView PATCH error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailByIdView(generics.RetrieveAPIView):
    """Get a single user's details by ID"""
    queryset = User.objects.all().select_related('userprofile')
    serializer_class = PublicUserSerializer 
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ UserDetailByIdView error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
# FOLLOW TOGGLE
# -------------------------------

class FollowToggleView(APIView):
    """
    Follow or unfollow a user by ID.
    Endpoint: /users/<pk>/follow_toggle/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            # 1. Retrieve the user being targeted (to follow/unfollow)
            # Use select_related here only if needed, but the primary user call is fine
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Prevent self-following
        if target_user == request.user:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 3. Get the target user's profile to access the 'followers' M2M field
            target_profile = target_user.userprofile

            # 4. Check the current following status
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

            # NOTE: M2M relationships (like followers.add/remove) automatically save the change, 
            # so target_profile.save() is typically NOT required here.

            # 6. Return the updated status and a success message
            return Response(
                {
                    "message": message, 
                    "is_following": not is_following, # The new status
                    "action": action
                }, 
                status=status.HTTP_200_OK
            )
        except UserProfile.DoesNotExist:
            return Response({"error": "Target user profile not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"❌ FollowToggleView error: {str(e)}")
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


# In projects/views.py - Update TransactionCreateView

class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Custom create to handle transaction logic properly"""
        try:
            receiver_id = request.data.get('receiver')
            project_id = request.data.get('project')
            amount = request.data.get('amount')

            # Validate inputs
            if not all([receiver_id, project_id, amount]):
                return Response(
                    {"error": "receiver, project, and amount are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get objects
            try:
                receiver = User.objects.get(id=receiver_id)
                project = Project.objects.get(id=project_id)
                amount = float(amount)
            except (User.DoesNotExist, Project.DoesNotExist, ValueError) as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sender = request.user

            # Perform transaction
            with transaction.atomic():
                sender_profile = sender.userprofile
                receiver_profile = receiver.userprofile

                if sender_profile.balance < amount:
                    return Response(
                        {"error": "Insufficient balance."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                sender_profile.balance -= amount
                receiver_profile.balance += amount
                project.current_funding += amount

                sender_profile.save()
                receiver_profile.save()
                project.save()

                # Create transaction record
                trans = Transaction.objects.create(
                    sender=sender,
                    receiver=receiver,
                    project=project,
                    amount=amount
                )

                serializer = self.get_serializer(trans)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"❌ Transaction error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        # ✅ FIX: Ensure we select related user profiles to avoid N+1 queries in the serializer
        return Conversation.objects.filter(
            models.Q(user1=self.request.user) | models.Q(user2=self.request.user)
        ).select_related('user1__userprofile', 'user2__userprofile')

    def perform_create(self, serializer):
        # We assume the incoming data includes 'user2' (the other user's ID)
        # The serializer should validate that 'user2' is present
        # user1 is automatically set to the requesting user
        serializer.save(user1=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        # ✅ FIX: Ensure we select related sender profile to avoid N+1 queries in the serializer
        # Also, filter by conversation AND ensure the user is part of that conversation for security
        
        user = self.request.user
        
        # Security Check: Ensure the user is part of the conversation
        conversation = Conversation.objects.filter(
            id=conversation_id
        ).filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).first()

        if not conversation:
            # Return empty queryset or raise exception if conversation is not found or user is not a participant
            return Message.objects.none()
            
        return Message.objects.filter(
            conversation_id=conversation_id
        ).select_related('sender__userprofile').order_by("timestamp")


    def perform_create(self, serializer):
        conversation_id = self.kwargs["conversation_id"]
        # This view's perform_create is robust: it injects sender and conversation_id
        serializer.save(sender=self.request.user, conversation_id=conversation_id)