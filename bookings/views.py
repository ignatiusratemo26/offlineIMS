from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta

from .models import Workspace, BookingSlot, EquipmentBooking, WorkspaceBooking
from .serializers import (
    WorkspaceSerializer, BookingSlotSerializer, 
    EquipmentBookingSerializer, EquipmentBookingCreateSerializer,
    WorkspaceBookingSerializer, WorkspaceBookingCreateSerializer
)
from users.permissions import IsAdminUser, IsLabManagerUser, IsTechnicianUser

class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lab', 'is_active']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'capacity']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminUser() | IsLabManagerUser() | IsTechnicianUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        workspace = self.get_object()
        date_param = request.query_params.get('date', date.today().isoformat())
        
        try:
            target_date = date.fromisoformat(date_param)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all slots for the date
        all_slots = BookingSlot.objects.filter(date=target_date)
        
        # Get booked slots for the workspace
        booked_slot_ids = WorkspaceBooking.objects.filter(
            workspace=workspace,
            slot__date=target_date,
            status__in=['PENDING', 'APPROVED']
        ).values_list('slot_id', flat=True)
        
        # Filter available slots
        available_slots = all_slots.exclude(id__in=booked_slot_ids)
        
        return Response(BookingSlotSerializer(available_slots, many=True).data)

class BookingSlotViewSet(viewsets.ModelViewSet):
    queryset = BookingSlot.objects.all()
    serializer_class = BookingSlotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'start_time']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminUser() | IsLabManagerUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        start_date_param = request.query_params.get('start_date', date.today().isoformat())
        end_date_param = request.query_params.get('end_date', (date.today() + timedelta(days=7)).isoformat())
        
        try:
            start_date = date.fromisoformat(start_date_param)
            end_date = date.fromisoformat(end_date_param)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slots = BookingSlot.objects.filter(date__gte=start_date, date__lte=end_date).order_by('date', 'start_time')
        return Response(BookingSlotSerializer(slots, many=True).data)

class EquipmentBookingViewSet(viewsets.ModelViewSet):
    queryset = EquipmentBooking.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'equipment', 'user']
    search_fields = ['purpose', 'project_name', 'notes']
    ordering_fields = ['created_at', 'slot__date', 'slot__start_time']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return EquipmentBookingCreateSerializer
        return EquipmentBookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and Lab Managers can see all bookings
        if user.is_admin or user.is_lab_manager:
            return EquipmentBooking.objects.all()
        
        # Technicians can see bookings for their lab
        if user.is_technician:
            return EquipmentBooking.objects.filter(equipment__lab=user.lab)
        
        # Students can only see their own bookings
        return EquipmentBooking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='PENDING')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can approve
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to approve bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'PENDING':
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'APPROVED'
        booking.approved_by = request.user
        booking.save()
        
        return Response(EquipmentBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can reject
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to reject bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'PENDING':
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'REJECTED'
        booking.approved_by = request.user
        booking.save()
        
        return Response(EquipmentBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Only the user who created the booking or an admin can cancel it
        if booking.user != request.user and not (request.user.is_admin or request.user.is_lab_manager):
            return Response(
                {"error": "You don't have permission to cancel this booking."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['PENDING', 'APPROVED']:
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'CANCELLED'
        booking.save()
        
        return Response(EquipmentBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can mark as completed
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to complete bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'APPROVED':
            return Response(
                {"error": "Only approved bookings can be marked as completed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'COMPLETED'
        booking.save()
        
        return Response(EquipmentBookingSerializer(booking).data)

class WorkspaceBookingViewSet(viewsets.ModelViewSet):
    queryset = WorkspaceBooking.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'workspace', 'user']
    search_fields = ['purpose', 'project_name', 'notes']
    ordering_fields = ['created_at', 'slot__date', 'slot__start_time']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return WorkspaceBookingCreateSerializer
        return WorkspaceBookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and Lab Managers can see all bookings
        if user.is_admin or user.is_lab_manager:
            return WorkspaceBooking.objects.all()
        
        # Technicians can see bookings for their lab
        if user.is_technician:
            return WorkspaceBooking.objects.filter(workspace__lab=user.lab)
        
        # Students can only see their own bookings
        return WorkspaceBooking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='PENDING')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can approve
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to approve bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'PENDING':
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'APPROVED'
        booking.approved_by = request.user
        booking.save()
        
        return Response(WorkspaceBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can reject
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to reject bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'PENDING':
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'REJECTED'
        booking.approved_by = request.user
        booking.save()
        
        return Response(WorkspaceBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Only the user who created the booking or an admin can cancel it
        if booking.user != request.user and not (request.user.is_admin or request.user.is_lab_manager):
            return Response(
                {"error": "You don't have permission to cancel this booking."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['PENDING', 'APPROVED']:
            return Response(
                {"error": f"Booking is already {booking.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'CANCELLED'
        booking.save()
        
        return Response(WorkspaceBookingSerializer(booking).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        booking = self.get_object()
        
        # Only Admin, Lab Manager, or Technician can mark as completed
        if not (request.user.is_admin or request.user.is_lab_manager or request.user.is_technician):
            return Response(
                {"error": "You don't have permission to complete bookings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'APPROVED':
            return Response(
                {"error": "Only approved bookings can be marked as completed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'COMPLETED'
        booking.save()
        
        return Response(WorkspaceBookingSerializer(booking).data)