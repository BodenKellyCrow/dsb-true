# projects/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Project, Transaction, UserProfile,
    SocialPost, Like, Comment,
    Conversation, Message
)
import logging
logger = logging.getLogger(__name__)


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
    
    bio = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'bio', 'profile_image']

    def get_bio(self, obj):
        try:
            return obj.userprofile.bio or ''
        except (AttributeError, UserProfile.DoesNotExist):
            return ''

    def get_profile_image(self, obj):
        try:
            if obj.userprofile.profile_image:
                # IMPORTANT: Return the file URL when accessed via HTTP (using .url)
                return obj.userprofile.profile_image.url 
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return None

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        UserProfile.objects.get_or_create(user=user)
        return user

    # ✅ FIX: Enhanced update method to correctly handle profile_image and bio
    def update(self, instance, validated_data):
        # 1. Handle User fields (like username)
        for attr, value in validated_data.items():
            if attr not in ['password']: # Exclude password and profile fields 
                setattr(instance, attr, value)
        
        # 2. Handle Password
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
            
        instance.save()

        # 3. Handle UserProfile fields (bio and profile_image)
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        
        # profile_image and bio are sent via self.initial_data (Form Data)
        if 'bio' in self.initial_data:
            profile.bio = self.initial_data['bio']
            
        # Check if a new image file was uploaded
        if 'profile_image' in self.initial_data and self.initial_data['profile_image']:
            # The uploaded file is in self.initial_data, not validated_data
            profile.profile_image = self.initial_data['profile_image']
        
        # Note: DRF handles deletion of old files when a new one is assigned

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

    # ✅ FIX 3: New method to check if the requesting user is following 'obj' (Fixes Priority 3 initialization)
    def get_is_following(self, obj):
        request = self.context.get('request')
        # Check if we have a request and a logged-in user
        if request and request.user.is_authenticated:
            # Prevent checking if the user is following themselves (though the view blocks this)
            if obj.id == request.user.id:
                return False
                
            try:
                # Check if the current user is in the target user's followers list.
                return obj.userprofile.followers.filter(id=request.user.id).exists()
            except (AttributeError, UserProfile.DoesNotExist):
                # Safety fallback
                pass
        return False

# -------------------
# PROJECTS + FUNDING
# -------------------
class ProjectSerializer(serializers.ModelSerializer):
    # Pass the request context down to PublicUserSerializer
    owner = PublicUserSerializer(read_only=True, context={'request': serializers.CurrentUserDefault()}) 
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
    # Ensure likes and comments are retrieved correctly if implemented in models
    likes = LikeSerializer(many=True, read_only=True) 
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = SocialPost
        fields = ['id', 'author', 'content', 'image', 'created_at', 'likes', 'comments']


# -------------------
# MESSAGING
# -------------------
# ✅ FIX: MessageSerializer now correctly maps fields for the chat system to work with views.py
class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        # Ensure 'text' is writeable, and 'conversation' is read/write
        fields = ['id', 'conversation', 'sender', 'sender_username', 'text', 'timestamp']
        read_only_fields = ['sender'] # Sender is set automatically in MessageListCreateView