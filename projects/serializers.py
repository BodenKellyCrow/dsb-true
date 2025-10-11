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

    # Flattened profile fields (for easy consumption)
    bio = serializers.CharField(source="profile.bio", required=False, allow_blank=True)
    profile_image = serializers.ImageField(source="profile.profile_image", required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'bio', 'profile_image']

    def create(self, validated_data):
        """
        Create a new User and ensure a UserProfile exists.
        Handle password properly if provided.
        """
        # Extract password if provided
        password = validated_data.pop("password", None)

        # Pop nested profile if present (we don't use it directly now)
        profile_data = validated_data.pop("profile", {}) if "profile" in validated_data else {}

        # Create user
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        # Ensure profile exists
        UserProfile.objects.get_or_create(user=user)

        return user

    def update(self, instance, validated_data):
        # Extract nested profile data
        profile_data = validated_data.pop("profile", {})
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
    bio = serializers.CharField(source="profile.bio", read_only=True)
    profile_image = serializers.ImageField(source="profile.profile_image", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'profile_image']


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
