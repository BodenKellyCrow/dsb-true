# projects/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Project, Transaction, UserProfile,
    SocialPost, Like, Comment,
    Conversation, Message
)


# -------------------
# USER + PROFILE
# -------------------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'balance', 'profile_image']
        read_only_fields = ['balance']


class UserSerializer(serializers.ModelSerializer):
    # allow frontend to send password on registration
    password = serializers.CharField(write_only=True, required=False)

    # Flattened profile fields (for easy consumption) - Source corrected to 'userprofile'
    bio = serializers.CharField(source="userprofile.bio", required=False, allow_blank=True)
    profile_image = serializers.ImageField(source="userprofile.profile_image", required=False, allow_null=True)

    # Add follow-related counts
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'bio', 'profile_image', 'follower_count', 'following_count']

    # --- Helper Methods for Counts ---
    def get_follower_count(self, obj):
        # Counts how many users follow this user (via UserProfile.followers)
        return obj.userprofile.followers.count()

    def get_following_count(self, obj):
        # Counts how many users this user is following (via User.following related_name)
        return obj.following.count()
    # ---------------------------------

    def create(self, validated_data):
        """
        Create a new User and ensure a UserProfile exists.
        Handle password properly if provided.
        """
        # Extract password if provided
        password = validated_data.pop("password", None)

        # Pop nested profile data (Source corrected to 'userprofile' for consistency)
        profile_data = validated_data.pop("userprofile", {}) if "userprofile" in validated_data else {}

        # Create user
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        # Ensure profile exists
        # NOTE: We don't populate bio/image on create here, assuming it's done via update or later
        UserProfile.objects.get_or_create(user=user)

        return user

    def update(self, instance, validated_data):
        # Extract nested profile data (Source corrected to 'userprofile')
        profile_data = validated_data.pop("userprofile", {})
        bio = validated_data.pop("bio", None)
        profile_image = validated_data.pop("profile_image", None)

        # Handle password update if provided
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        # Update remaining user fields
        instance = super().update(instance, validated_data)
        instance.save()

        # Ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(user=instance)

        # Update profile fields
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
        if bio is not None:
            profile.bio = bio
        if profile_image is not None:
            profile.profile_image = profile_image
        profile.save()

        return instance


class PublicUserSerializer(serializers.ModelSerializer):
    # Flattened profile fields (Source corrected to 'userprofile')
    bio = serializers.CharField(source="userprofile.bio", read_only=True)
    profile_image = serializers.ImageField(source="userprofile.profile_image", read_only=True)

    # Add follow-related fields
    is_followed_by_current_user = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'profile_image', 
                  'is_followed_by_current_user', 'follower_count', 'following_count']

    # --- Helper Methods for Follower Logic ---
    def get_is_followed_by_current_user(self, obj):
        """Checks if the request.user is following the user being viewed (obj)."""
        request = self.context.get('request', None)

        if request and request.user.is_authenticated:
            current_user = request.user
            # Check if the user being viewed (obj) has the current_user in its followers list
            return obj.userprofile.followers.filter(id=current_user.id).exists()
        return False
    
    def get_follower_count(self, obj):
        # Counts how many users follow this user
        return obj.userprofile.followers.count()

    def get_following_count(self, obj):
        # Counts how many users this user is following
        return obj.following.count()
    # -----------------------------------------


# -------------------
# PROJECTS + FUNDING
# -------------------
class ProjectSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'image',
            'funding_goal', 'current_funding',
            'owner', 'owner_username'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'


# -------------------
# SOCIAL POSTS
# -------------------
class CommentSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'created_at']


class SocialPostSerializer(serializers.ModelSerializer):
    author = PublicUserSerializer(read_only=True)
    likes = LikeSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = SocialPost
        fields = ['id', 'author', 'content', 'image', 'created_at', 'likes', 'comments']


# -------------------
# MESSAGING
# -------------------
class ConversationSerializer(serializers.ModelSerializer):
    user1_username = serializers.CharField(source='user1.username', read_only=True)
    user2_username = serializers.CharField(source='user2.username', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user1', 'user2', 'user1_username', 'user2_username', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_username', 'text', 'timestamp']