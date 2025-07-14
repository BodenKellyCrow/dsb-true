from .models import Project, Transaction
from .serializers import ProjectSerializer, TransactionSerializer
from rest_framework import viewsets, permissions
from .models import Project, Transaction, UserProfile
from .serializers import ProjectSerializer, TransactionSerializer, UserProfileSerializer
from rest_framework.exceptions import ValidationError


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
