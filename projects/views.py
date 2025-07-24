from .models import Project, Transaction
from .serializers import ProjectSerializer, TransactionSerializer, PublicUserSerializer
from rest_framework import viewsets, permissions
from .models import Project, Transaction, UserProfile
from .serializers import ProjectSerializer, TransactionSerializer, UserProfileSerializer
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import SocialPost, Like, Comment, Conversation, Message
from .serializers import SocialPostSerializer, CommentSerializer, ConversationSerializer, MessageSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q

User = get_user_model()

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by('-timestamp')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.validated_data['receiver']
        project = serializer.validated_data['project']
        amount = serializer.validated_data['amount']

        # Safety checks
        if sender == receiver:
            raise ValidationError("You cannot send money to yourself.")
        if amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero.")
        if sender.profile.balance < amount:
            raise ValidationError("Insufficient funds.")

        # Save transaction
        transaction = serializer.save(sender=sender)

        # Update project funding
        project.current_funding += amount
        project.save()

        # Update balances
        sender.profile.balance -= amount
        sender.profile.save()

        receiver.profile.balance += amount
        receiver.profile.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserProjectsView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Project.objects.filter(owner__id=user_id)


class UserFundedProjectsView(APIView):
    def get(self, request, user_id):
        funded_project_ids = Transaction.objects.filter(
            sender__id=user_id
        ).values_list('project__id', flat=True).distinct()
        projects = Project.objects.filter(id__in=funded_project_ids)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
    
class UserProfileUpdateView(generics.UpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
    
class SocialPostListCreateView(generics.ListCreateAPIView):
    queryset = SocialPost.objects.all().order_by('-created_at')
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class FeedView(generics.ListAPIView):
    queryset = SocialPost.objects.all().order_by('-created_at')
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticated]

class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = SocialPost.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()  # toggle
        return Response({'liked': created})

class AddCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = SocialPost.objects.get(id=post_id)
        comment = Comment.objects.create(
            post=post, user=request.user, content=request.data.get("content", "")
        )
        return Response(CommentSerializer(comment).data)
    
class UserTransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(sender=request.user).select_related('project')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)    

class PublicUserListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        users = User.objects.all()
        serializer = PublicUserSerializer(users, many=True)
        return Response(serializer.data)

class UserConversationsView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(user1=user) | Q(user2=user))

class CreateConversationView(generics.CreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user1 = request.user
        user2_id = request.data.get('user2')

        if not user2_id:
            return Response({'error': 'user2 is required'}, status=400)

        # Ensure user2 exists
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=404)

        # Order users to maintain consistency
        ordered_users = sorted([user1.id, user2.id])
        existing = Conversation.objects.filter(user1_id=ordered_users[0], user2_id=ordered_users[1]).first()

        if existing:
            serializer = self.get_serializer(existing)
            return Response(serializer.data)

        conversation = Conversation.objects.create(user1_id=ordered_users[0], user2_id=ordered_users[1])
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(conversation_id=conversation_id).order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)