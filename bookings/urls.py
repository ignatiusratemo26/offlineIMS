from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpRequest
from .views import (
    WorkspaceViewSet, BookingSlotViewSet, EquipmentBookingViewSet, 
    WorkspaceBookingViewSet, CalendarView, MyBookingsView,
    ResourceAvailabilityView, BookingsListView
)

# Create a class for handling generic bookings
class BookingCreateRouter(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Store the data from request.data before it gets consumed
        resource_type = request.data.get('resource_type')
        data = request.data.copy()
        
        if resource_type == 'EQUIPMENT':
            # Create a new serializer and validate it
            from .serializers import EquipmentBookingCreateSerializer
            serializer = EquipmentBookingCreateSerializer(data=data)
            if serializer.is_valid():
                booking = serializer.save(user=request.user, status='PENDING')
                from .serializers import EquipmentBookingSerializer
                return Response(EquipmentBookingSerializer(booking).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif resource_type == 'WORKSPACE':
            # Create a new serializer and validate it
            from .serializers import WorkspaceBookingCreateSerializer
            serializer = WorkspaceBookingCreateSerializer(data=data)
            if serializer.is_valid():
                booking = serializer.save(user=request.user, status='PENDING')
                from .serializers import WorkspaceBookingSerializer
                return Response(WorkspaceBookingSerializer(booking).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response(
                {"error": "Invalid resource_type. Must be 'EQUIPMENT' or 'WORKSPACE'."},
                status=status.HTTP_400_BAD_REQUEST
            )

class BookingsRouter(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Forward to BookingsListView
        return BookingsListView().get(request)
        
    def post(self, request):
        # Forward to BookingCreateRouter
        return BookingCreateRouter().post(request)
    

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet)
router.register(r'slots', BookingSlotViewSet)
router.register(r'equipment-bookings', EquipmentBookingViewSet)
router.register(r'workspace-bookings', WorkspaceBookingViewSet)

urlpatterns = [
    path('', BookingsRouter.as_view()),  # Add this line for root POST requests
    path('', include(router.urls)),
    path('calendar/', CalendarView.as_view(), name='booking-calendar'),
    path('my_bookings/', MyBookingsView.as_view(), name='my-bookings'),
    path('availability/', ResourceAvailabilityView.as_view(), name='resource-availability'),
]