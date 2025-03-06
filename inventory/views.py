from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import OR
from django.utils import timezone
from .models import Category, Equipment, MaintenanceRecord, EquipmentUsageLog, EquipmentTransfer
from .serializers import (
    CategorySerializer, EquipmentSerializer, EquipmentDetailSerializer,
    MaintenanceRecordSerializer, EquipmentUsageLogSerializer, EquipmentTransferSerializer
)
from users.permissions import IsAdminUser, IsLabManagerUser, IsTechnicianUser

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
        return [permissions.IsAuthenticated()]

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'serial_number', 'barcode', 'status']
    ordering_fields = ['name', 'status', 'lab', 'category']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EquipmentDetailSerializer
        return EquipmentSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Equipment.objects.all()
        # Filter by lab if specified
        lab = self.request.query_params.get('lab')
        if lab:
            queryset = queryset.filter(lab=lab)
        
        # Filter by status if specified
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by category if specified
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        equipment = self.get_object()
        
        if equipment.status != 'AVAILABLE':
            return Response(
                {"error": f"Equipment is currently {equipment.status.lower()}, not available for checkout."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EquipmentUsageLogSerializer(data={
            'equipment': equipment.id,
            'user': request.user.id,
            'check_out_time': timezone.now(),
            'purpose': request.data.get('purpose', '')
        })
        
        if serializer.is_valid():
            serializer.save()
            equipment.status = 'IN_USE'
            equipment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        equipment = self.get_object()
        
        if equipment.status != 'IN_USE':
            return Response(
                {"error": "Equipment is not currently checked out."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find the most recent usage log without a check-in time
        usage_log = EquipmentUsageLog.objects.filter(
            equipment=equipment,
            check_in_time__isnull=True
        ).order_by('-check_out_time').first()
        
        if not usage_log:
            return Response(
                {"error": "No active checkout found for this equipment."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usage_log.check_in_time = timezone.now()
        usage_log.notes = request.data.get('notes', '')
        usage_log.save()
        
        equipment.status = 'AVAILABLE'
        equipment.save()
        
        return Response(EquipmentUsageLogSerializer(usage_log).data)
    
    @action(detail=True, methods=['post'])
    def schedule_maintenance(self, request, pk=None):
        equipment = self.get_object()
        
        serializer = MaintenanceRecordSerializer(data={
            'equipment': equipment.id,
            'maintenance_date': request.data.get('maintenance_date'),
            'description': request.data.get('description'),
            'performed_by': request.user.id,
            'notes': request.data.get('notes', '')
        })
        
        if serializer.is_valid():
            serializer.save()
            equipment.status = 'MAINTENANCE'
            equipment.next_maintenance_date = request.data.get('maintenance_date')
            equipment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete_maintenance(self, request, pk=None):
        equipment = self.get_object()
        
        maintenance_id = request.data.get('maintenance_id')
        if not maintenance_id:
            return Response(
                {"error": "Maintenance ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            maintenance = MaintenanceRecord.objects.get(id=maintenance_id, equipment=equipment)
        except MaintenanceRecord.DoesNotExist:
            return Response(
                {"error": "Maintenance record not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        maintenance.is_completed = True
        maintenance.notes = request.data.get('notes', maintenance.notes)
        maintenance.save()
        
        equipment.status = 'AVAILABLE'
        equipment.last_maintenance_date = timezone.now().date()
        equipment.next_maintenance_date = None
        equipment.save()
        
        return Response(MaintenanceRecordSerializer(maintenance).data)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        equipment = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        equipment.image = image_file
        equipment.save()
        
        return Response(
            {"message": "Image uploaded successfully", "equipment": EquipmentSerializer(equipment).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        equipment = self.get_object()
        to_lab = request.data.get('to_lab')
        
        if not to_lab:
            return Response(
                {"error": "Destination lab is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if equipment.lab == to_lab:
            return Response(
                {"error": "Equipment is already in this lab."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EquipmentTransferSerializer(data={
            'equipment': equipment.id,
            'from_lab': equipment.lab,
            'to_lab': to_lab,
            'transferred_by': request.user.id,
            'transfer_date': timezone.now(),
            'notes': request.data.get('notes', '')
        })
        
        if serializer.is_valid():
            serializer.save()
            equipment.lab = to_lab
            equipment.status = 'SHARED'
            equipment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment__name', 'description']
    ordering_fields = ['maintenance_date', 'is_completed']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = MaintenanceRecord.objects.all()
        
        # Filter by equipment if specified
        equipment_id = self.request.query_params.get('equipment')
        if equipment_id:
            queryset = queryset.filter(equipment__id=equipment_id)
            
        # Filter by completion status if specified
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            is_completed = is_completed.lower() == 'true'
            queryset = queryset.filter(is_completed=is_completed)
            
        return queryset

class EquipmentUsageLogViewSet(viewsets.ModelViewSet):
    queryset = EquipmentUsageLog.objects.all()
    serializer_class = EquipmentUsageLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment__name', 'user__username', 'purpose']
    ordering_fields = ['check_out_time', 'check_in_time']

    def get_queryset(self):
        queryset = EquipmentUsageLog.objects.all()
        
        # Filter by equipment if specified
        equipment_id = self.request.query_params.get('equipment')
        if equipment_id:
            queryset = queryset.filter(equipment__id=equipment_id)
            
        # Filter by user if specified
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user__id=user_id)
            
        # Filter active checkouts (no check-in time)
        active = self.request.query_params.get('active')
        if active is not None:
            active = active.lower() == 'true'
            if active:
                queryset = queryset.filter(check_in_time__isnull=True)
            else:
                queryset = queryset.filter(check_in_time__isnull=False)
                
        return queryset

class EquipmentTransferViewSet(viewsets.ModelViewSet):
    queryset = EquipmentTransfer.objects.all()
    serializer_class = EquipmentTransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment__name', 'from_lab', 'to_lab']
    ordering_fields = ['transfer_date', 'return_date']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = EquipmentTransfer.objects.all()
        
        # Filter by equipment if specified
        equipment_id = self.request.query_params.get('equipment')
        if equipment_id:
            queryset = queryset.filter(equipment__id=equipment_id)
            
        # Filter by lab if specified
        lab = self.request.query_params.get('lab')
        if lab:
            queryset = queryset.filter(from_lab=lab) | queryset.filter(to_lab=lab)
            
        # Filter by active transfers (no return date)
        active = self.request.query_params.get('active')
        if active is not None:
            active = active.lower() == 'true'
            if active:
                queryset = queryset.filter(return_date__isnull=True)
            else:
                queryset = queryset.filter(return_date__isnull=False)
                
        return queryset