from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Project, Transaction
from .serializers import ProjectSerializer, TransactionSerializer

@api_view(['GET'])
def project_list(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def project_detail(request, pk):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=404)
    
    serializer = ProjectSerializer(project)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fund_project(request, pk):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=404)

    amount = request.data.get('amount')
    if not amount:
        return Response({'error': 'Amount is required'}, status=400)

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return Response({'error': 'Invalid amount'}, status=400)

    transaction = Transaction.objects.create(
        sender=request.user,
        recipient=project.owner,
        project=project,
        amount=amount,
    )

    project.amount_raised += amount
    project.save()

    return Response(TransactionSerializer(transaction).data, status=201)
