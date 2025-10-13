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
    password = serializers.CharField(write_only=True, required=False)
    
    # ✅ CRITICAL FIX: Use SerializerMethodField to safely handle missing profiles
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'bio', 'profile_image', 'follower_count', 'following_count']

    # ✅ Safe getter methods that handle missing profiles
    def get_bio(self, obj):
        """Safely get bio, return empty string if no profile"""
        return getattr(obj.userprofile, 'bio', '') if hasattr(obj, 'userprofile') else ''

    def get_profile_image(self, obj):
        """Safely get profile image, return None if no profile"""
        if hasattr(obj, 'userprofile') and obj.userprofile.profile_image:
            return obj.userprofile.profile_image.url
        return None

    def get_follower_count(self, obj):
        """Safely get follower count"""
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.followers.count()
        return 0

    def get_following_count(self, obj):
        """Safely get following count"""
        return obj.following.count() if hasattr(obj, 'following') else 0

    def create(self, validated_data):
        """Create user and ensure profile exists"""
        password = validated_data.pop("password", None)
        
        # Create user
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        # ✅ ALWAYS create profile
        UserProfile.objects.get_or_create(user=user)

        return user

    def update(self, instance, validated_data):
        """Update user and profile"""
        # Handle password
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        # Extract profile-related data from request
        bio = self.initial_data.get('bio', None)
        profile_image = self.initial_data.get('profile_image', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ✅ Ensure profile exists
        profile, created = UserProfile.objects.get_or_create(user=instance)

        # Update profile fields
        if bio is not None:
            profile.bio = bio
        if profile_image is not None:
            profile.profile_image = profile_image
        profile.save()

        return instance


class PublicUserSerializer(serializers.ModelSerializer):
    # ✅ Use SerializerMethodField for safe access
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    is_followed_by_current_user = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'profile_image', 
                  'is_followed_by_current_user', 'follower_count', 'following_count']

    def get_bio(self, obj):
        return getattr(obj.userprofile, 'bio', '') if hasattr(obj, 'userprofile') else ''

    def get_profile_image(self, obj):
        if hasattr(obj, 'userprofile') and obj.userprofile.profile_image:
            return obj.userprofile.profile_image.url
        return None

    def get_is_followed_by_current_user(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            if hasattr(obj, 'userprofile'):
                return obj.userprofile.followers.filter(id=request.user.id).exists()
        return False
    
    def get_follower_count(self, obj):
        return obj.userprofile.followers.count() if hasattr(obj, 'userprofile') else 0

    def get_following_count(self, obj):
        return obj.following.count() if hasattr(obj, 'following') else 0


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
            'owner', 'owner_username', 'created_at'
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