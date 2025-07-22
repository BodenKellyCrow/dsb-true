from .models import Project, Transaction
from .serializers import ProjectSerializer, TransactionSerializer
from rest_framework import viewsets, permissions
from .models import Project, Transaction, UserProfile
from .serializers import ProjectSerializer, TransactionSerializer, UserProfileSerializer
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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