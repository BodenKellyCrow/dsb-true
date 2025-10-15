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
    
    # ✅ Use SerializerMethodField to safely handle missing profiles
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'bio', 'profile_image']

    def get_bio(self, obj):
        """Safely get bio, return empty string if no profile"""
        try:
            return obj.userprofile.bio or ''
        except (AttributeError, UserProfile.DoesNotExist):
            return ''

    def get_profile_image(self, obj):
        """Safely get profile image URL, return None if no profile"""
        try:
            if obj.userprofile.profile_image:
                return obj.userprofile.profile_image.url
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None

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

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ✅ Ensure profile exists and update it
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        
        # Check for bio and profile_image in initial_data (from form)
        if 'bio' in self.initial_data:
            profile.bio = self.initial_data['bio']
        if 'profile_image' in self.initial_data and self.initial_data['profile_image']:
            profile.profile_image = self.initial_data['profile_image']
        profile.save()

        return instance


# projects/serializers.py

# ... (around line 98)

class PublicUserSerializer(serializers.ModelSerializer):
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    
    # ✅ FIX 1: Add is_following field
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        # ✅ FIX 2: Add is_following to fields
        fields = ['id', 'username', 'bio', 'profile_image', 'is_following']

    def get_bio(self, obj):
        try:
            return obj.userprofile.bio or ''
        except (AttributeError, UserProfile.DoesNotExist):
            return ''

    def get_profile_image(self, obj):
        try:
            if obj.userprofile.profile_image:
                return obj.userprofile.profile_image.url
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None

    # ✅ FIX 3: New method to check if the requesting user is following 'obj'
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if the currently viewed user (obj) has the requesting user (request.user) in their followers list.
            try:
                # Assuming UserProfile has a 'followers' Many-to-Many field pointing to User
                return obj.userprofile.followers.filter(id=request.user.id).exists()
            except (AttributeError, UserProfile.DoesNotExist):
                # Should not happen with the previous fix, but safe check
                pass
        return False

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