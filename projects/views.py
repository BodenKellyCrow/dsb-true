from .models import Project, Transaction
from .serializers import ProjectSerializer, TransactionSerializer
from rest_framework import viewsets, permissions
from .models import Project, Transaction, UserProfile
from .serializers import ProjectSerializer, TransactionSerializer, UserProfileSerializer


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
        # Custom logic: deduct from sender, add to receiver/project
        transaction = serializer.save(sender=self.request.user)

        # Update project funding
        project = transaction.project
        project.current_funding += transaction.amount
        project.save()

        # Update user balances if needed (optional)
        sender_profile = self.request.user.profile
        receiver_profile = transaction.receiver.profile
        sender_profile.balance -= transaction.amount
        receiver_profile.balance += transaction.amount
        sender_profile.save()
        receiver_profile.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
