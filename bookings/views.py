from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from datetime import date, timedelta
from rest_framework.permissions import OR

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
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
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
            return [
                permissions.IsAuthenticated(),
                OR(IsAdminUser(), OR(IsLabManagerUser(), IsTechnicianUser()))
            ]
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
        
    @action(detail=False, methods=['get', 'post'])
    def find_or_create(self, request):
        # Get parameters
        date_param = request.query_params.get('date') or request.data.get('date')
        start_time_param = request.query_params.get('start_time') or request.data.get('start_time')
        end_time_param = request.query_params.get('end_time') or request.data.get('end_time')
        
        # Validate parameters
        if not all([date_param, start_time_param, end_time_param]):
            return Response(
                {"error": "Missing required parameters: date, start_time, end_time"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date
        try:
            booking_date = date.fromisoformat(date_param)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse times
        try:
            from datetime import datetime
            start_time = datetime.strptime(start_time_param, '%H:%M:%S').time()
            end_time = datetime.strptime(end_time_param, '%H:%M:%S').time()
        except ValueError:
            return Response(
                {"error": "Invalid time format. Please use HH:MM:SS."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if start time is before end time
        if start_time >= end_time:
            return Response(
                {"error": "Start time must be before end time."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find an existing slot
        try:
            slot = BookingSlot.objects.get(
                date=booking_date,
                start_time=start_time,
                end_time=end_time
            )
            created = False
        except BookingSlot.DoesNotExist:
            # Create a new slot if permission allows
            if request.user.is_admin or request.user.is_lab_manager:
                slot = BookingSlot.objects.create(
                    date=booking_date,
                    start_time=start_time,
                    end_time=end_time
                )
                created = True
            else:
                return Response(
                    {"error": "Slot not found and you don't have permission to create new slots."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({
            "slot": BookingSlotSerializer(slot).data,
            "created": created
        })


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
    


from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta, datetime
from users.permissions import IsAdminUser, IsLabManagerUser, IsTechnicianUser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.urls import path

# Add this class for the calendar endpoint
class CalendarView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Parse date range parameters
        start_date_str = request.query_params.get('start')
        end_date_str = request.query_params.get('end')
        resource_type = request.query_params.get('resource_type')
        equipment_id = request.query_params.get('equipment_id')
        workspace_id = request.query_params.get('workspace_id')
        status_param = request.query_params.get('status')
        lab = request.query_params.get('lab')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else (date.today() + timedelta(days=30))
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize result
        calendar_events = []
        
        # Get equipment bookings
        equipment_bookings = EquipmentBooking.objects.filter(
            slot__date__gte=start_date,
            slot__date__lte=end_date
        )
        
        # Apply filters for equipment bookings
        if status_param:
            equipment_bookings = equipment_bookings.filter(status=status_param)
        
        if equipment_id:
            equipment_bookings = equipment_bookings.filter(equipment_id=equipment_id)
        
        if lab:
            equipment_bookings = equipment_bookings.filter(equipment__lab=lab)
        
        # Get workspace bookings
        workspace_bookings = WorkspaceBooking.objects.filter(
            slot__date__gte=start_date,
            slot__date__lte=end_date
        )
        
        # Apply filters for workspace bookings
        if status_param:
            workspace_bookings = workspace_bookings.filter(status=status_param)
        
        if workspace_id:
            workspace_bookings = workspace_bookings.filter(workspace_id=workspace_id)
        
        if lab:
            workspace_bookings = workspace_bookings.filter(workspace__lab=lab)
        
        # Filter by resource type if specified
        if resource_type == 'EQUIPMENT':
            workspace_bookings = WorkspaceBooking.objects.none()
        elif resource_type == 'WORKSPACE':
            equipment_bookings = EquipmentBooking.objects.none()
        
        # Process equipment bookings
        for booking in equipment_bookings:
            slot = booking.slot
            event = {
                'id': f"equipment_{booking.id}",
                'title': f"{booking.equipment.name} - {booking.user.get_full_name()}",
                'start': f"{slot.date}T{slot.start_time}",
                'end': f"{slot.date}T{slot.end_time}",
                'resourceType': 'EQUIPMENT',
                'resourceId': booking.equipment.id,
                'resourceName': booking.equipment.name,
                'status': booking.status,
                'userId': booking.user.id,
                'userName': booking.user.get_full_name(),
                'lab': booking.equipment.lab,
                'purpose': booking.purpose,
                'projectName': booking.project_name,
                'notes': booking.notes,
                'color': self._get_status_color(booking.status)
            }
            calendar_events.append(event)
        
        # Process workspace bookings
        for booking in workspace_bookings:
            slot = booking.slot
            event = {
                'id': f"workspace_{booking.id}",
                'title': f"{booking.workspace.name} - {booking.user.get_full_name()}",
                'start': f"{slot.date}T{slot.start_time}",
                'end': f"{slot.date}T{slot.end_time}",
                'resourceType': 'WORKSPACE',
                'resourceId': booking.workspace.id,
                'resourceName': booking.workspace.name,
                'status': booking.status,
                'userId': booking.user.id,
                'userName': booking.user.get_full_name(),
                'lab': booking.workspace.lab,
                'purpose': booking.purpose,
                'projectName': booking.project_name,
                'participantsCount': booking.participants_count,
                'notes': booking.notes,
                'color': self._get_status_color(booking.status)
            }
            calendar_events.append(event)
        
        return Response(calendar_events)
    
    def _get_status_color(self, status):
        """Return a color code for each booking status."""
        status_colors = {
            'PENDING': '#FFC107',   # Yellow
            'APPROVED': '#4CAF50',  # Green
            'REJECTED': '#F44336',  # Red
            'CANCELLED': '#9E9E9E', # Gray
            'COMPLETED': '#2196F3'  # Blue
        }
        return status_colors.get(status, '#9C27B0')  # Default purple


class MyBookingsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = MyBookingsPagination
    
    def get(self, request):
        # Get query parameters
        search = request.query_params.get('search', '')
        status = request.query_params.get('status', '')
        resource_type = request.query_params.get('resource_type', '')
        lab = request.query_params.get('lab', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Get user's equipment bookings
        equipment_bookings = EquipmentBooking.objects.filter(user=request.user)
        
        # Apply filters
        if search:
            equipment_bookings = equipment_bookings.filter(
                Q(equipment__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(project_name__icontains=search)
            )
        
        if status:
            equipment_bookings = equipment_bookings.filter(status=status)
            
        if lab:
            equipment_bookings = equipment_bookings.filter(equipment__lab=lab)
            
        # Get user's workspace bookings
        workspace_bookings = WorkspaceBooking.objects.filter(user=request.user)
        
        # Apply filters
        if search:
            workspace_bookings = workspace_bookings.filter(
                Q(workspace__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(project_name__icontains=search)
            )
        
        if status:
            workspace_bookings = workspace_bookings.filter(status=status)
            
        if lab:
            workspace_bookings = workspace_bookings.filter(workspace__lab=lab)
            
        # Filter by resource type
        if resource_type == 'EQUIPMENT':
            workspace_bookings = WorkspaceBooking.objects.none()
        elif resource_type == 'WORKSPACE':
            equipment_bookings = EquipmentBooking.objects.none()
            
        # Serialize bookings
        equipment_data = EquipmentBookingSerializer(equipment_bookings, many=True).data
        workspace_data = WorkspaceBookingSerializer(workspace_bookings, many=True).data
        
        # Combine results
        all_bookings = []
        
        for booking in equipment_data:
            booking['resource_type'] = 'EQUIPMENT'
            all_bookings.append(booking)
            
        for booking in workspace_data:
            booking['resource_type'] = 'WORKSPACE'
            all_bookings.append(booking)
            
        # Sort by date
        all_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Paginate results
        start = (page - 1) * page_size
        end = start + page_size
        paginated_bookings = all_bookings[start:end]
        
        return Response({
            'results': paginated_bookings,
            'count': len(all_bookings),
            'next': f"/api/bookings/my_bookings/?page={page+1}&page_size={page_size}" if end < len(all_bookings) else None,
            'previous': f"/api/bookings/my_bookings/?page={page-1}&page_size={page_size}" if page > 1 else None,
        })
    


class ResourceAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get parameters from the request
        resource_type = request.query_params.get('resource_type')
        resource_id = request.query_params.get('resource_id')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        
        # Validate parameters
        if not all([resource_type, resource_id, start_time_str, end_time_str]):
            return Response(
                {"error": "Missing required parameters: resource_type, resource_id, start_time, end_time"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse timestamps
        try:
            # Parse the datetime strings
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            # Extract the date and time components
            start_date = start_time.date()
            start_time_only = start_time.time()
            end_date = end_time.date()
            end_time_only = end_time.time()
            
        except ValueError:
            return Response(
                {"error": "Invalid datetime format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the resource is available
        if resource_type == 'EQUIPMENT':
            # Check if equipment exists
            try:
                from inventory.models import Equipment
                equipment = Equipment.objects.get(id=resource_id)
            except Equipment.DoesNotExist:
                return Response(
                    {"error": "Equipment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if equipment status allows booking
            if equipment.status not in ['AVAILABLE', 'IN_USE']:
                return Response(
                    {
                        "available": False,
                        "reason": f"Equipment is currently {equipment.get_status_display()}"
                    }
                )
            
            # Find all slots in the time range
            slots = BookingSlot.objects.filter(
                date__range=[start_date, end_date],
                start_time__gte=start_time_only if start_date == end_date else '00:00:00',
                end_time__lte=end_time_only if start_date == end_date else '23:59:59'
            )
            
            # Check for existing bookings
            existing_bookings = EquipmentBooking.objects.filter(
                equipment_id=resource_id,
                slot__in=slots,
                status__in=['PENDING', 'APPROVED']
            )
            
            if existing_bookings.exists():
                return Response(
                    {
                        "available": False,
                        "reason": "Equipment is already booked during this time period"
                    }
                )
            
        elif resource_type == 'WORKSPACE':
            # Check if workspace exists
            try:
                workspace = Workspace.objects.get(id=resource_id)
            except Workspace.DoesNotExist:
                return Response(
                    {"error": "Workspace not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if workspace is active
            if not workspace.is_active:
                return Response(
                    {
                        "available": False,
                        "reason": "Workspace is currently inactive"
                    }
                )
            
            # Find all slots in the time range
            slots = BookingSlot.objects.filter(
                date__range=[start_date, end_date],
                start_time__gte=start_time_only if start_date == end_date else '00:00:00',
                end_time__lte=end_time_only if start_date == end_date else '23:59:59'
            )
            
            # Check for existing bookings
            existing_bookings = WorkspaceBooking.objects.filter(
                workspace_id=resource_id,
                slot__in=slots,
                status__in=['PENDING', 'APPROVED']
            )
            
            if existing_bookings.exists():
                return Response(
                    {
                        "available": False,
                        "reason": "Workspace is already booked during this time period"
                    }
                )
            
        else:
            return Response(
                {"error": "Invalid resource_type. Must be 'EQUIPMENT' or 'WORKSPACE'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If we get here, the resource is available
        return Response({"available": True})
    
class BookingsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get query parameters
        search = request.query_params.get('search', '')
        status_param = request.query_params.get('status', '')
        resource_type = request.query_params.get('resource_type', '')
        lab = request.query_params.get('lab', '')
        
        try:
            page = int(request.query_params.get('page', '1'))
            page_size = int(request.query_params.get('page_size', '10'))
        except ValueError:
            page = 1
            page_size = 10
        
        user = request.user
        
        # Get equipment bookings
        if user.is_admin or user.is_lab_manager:
            equipment_bookings = EquipmentBooking.objects.all()
        elif user.is_technician:
            equipment_bookings = EquipmentBooking.objects.filter(equipment__lab=user.lab)
        else:
            equipment_bookings = EquipmentBooking.objects.filter(user=user)
        
        # Apply filters
        if search:
            equipment_bookings = equipment_bookings.filter(
                Q(equipment__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(project_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        if status_param:
            equipment_bookings = equipment_bookings.filter(status=status_param)
            
        if lab:
            equipment_bookings = equipment_bookings.filter(equipment__lab=lab)
        
        # Get workspace bookings
        if user.is_admin or user.is_lab_manager:
            workspace_bookings = WorkspaceBooking.objects.all()
        elif user.is_technician:
            workspace_bookings = WorkspaceBooking.objects.filter(workspace__lab=user.lab)
        else:
            workspace_bookings = WorkspaceBooking.objects.filter(user=user)
        
        # Apply filters
        if search:
            workspace_bookings = workspace_bookings.filter(
                Q(workspace__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(project_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        if status_param:
            workspace_bookings = workspace_bookings.filter(status=status_param)
            
        if lab:
            workspace_bookings = workspace_bookings.filter(workspace__lab=lab)
            
        # Filter by resource type if specified
        if resource_type == 'EQUIPMENT':
            workspace_bookings = WorkspaceBooking.objects.none()
        elif resource_type == 'WORKSPACE':
            equipment_bookings = EquipmentBooking.objects.none()
            
        # Serialize bookings
        equipment_data = EquipmentBookingSerializer(equipment_bookings, many=True).data
        workspace_data = WorkspaceBookingSerializer(workspace_bookings, many=True).data
        
        # Combine results
        all_bookings = []
        
        for booking in equipment_data:
            booking['resource_type'] = 'EQUIPMENT'
            all_bookings.append(booking)
            
        for booking in workspace_data:
            booking['resource_type'] = 'WORKSPACE'
            all_bookings.append(booking)
            
        # Sort by created_at (newest first)
        all_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Total count before pagination
        total_count = len(all_bookings)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_bookings = all_bookings[start:end]
        
        # Build pagination URLs
        base_url = "/api/bookings/"
        query_params = request.query_params.copy()
        
        # Calculate next page URL
        next_page_url = None
        if end < total_count:
            query_params['page'] = page + 1
            next_page_url = f"{base_url}?{query_params.urlencode()}"
        
        # Calculate previous page URL
        previous_page_url = None
        if page > 1:
            query_params['page'] = page - 1
            previous_page_url = f"{base_url}?{query_params.urlencode()}"
        
        return Response({
            'results': paginated_bookings,
            'count': total_count,
            'next': next_page_url,
            'previous': previous_page_url,
        })