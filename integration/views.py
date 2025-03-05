from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import json

from .models import LabIntegration, SharedResource, SyncLog, DataSyncQueue
from .serializers import (
    LabIntegrationSerializer, SharedResourceSerializer,
    SyncLogSerializer, DataSyncQueueSerializer
)
from users.permissions import IsAdminUser, IsLabManagerUser

class LabIntegrationViewSet(viewsets.ModelViewSet):
    queryset = LabIntegration.objects.all()
    serializer_class = LabIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lab_name', 'is_active']
    search_fields = ['lab_name', 'ip_address']
    ordering_fields = ['lab_name', 'last_sync']

class SharedResourceViewSet(viewsets.ModelViewSet):
    queryset = SharedResource.objects.all()
    serializer_class = SharedResourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsLabManagerUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resource_type', 'owner_lab', 'shared_with_lab']
    search_fields = ['resource_name']
    ordering_fields = ['resource_name', 'created_at']

class SyncLogViewSet(viewsets.ModelViewSet):
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_lab', 'target_lab', 'status']
    search_fields = ['source_lab', 'target_lab']
    ordering_fields = ['sync_time', 'status']

class DataSyncQueueViewSet(viewsets.ModelViewSet):
    queryset = DataSyncQueue.objects.all()
    serializer_class = DataSyncQueueSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_lab', 'target_lab', 'sync_type', 'status']
    search_fields = ['source_lab', 'target_lab', 'sync_type']
    ordering_fields = ['created_at', 'status']