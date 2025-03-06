from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkspaceViewSet,
    BookingSlotViewSet,
    EquipmentBookingViewSet,
    WorkspaceBookingViewSet,
    CalendarView
)

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet)
router.register(r'slots', BookingSlotViewSet)
router.register(r'equipment-bookings', EquipmentBookingViewSet)
router.register(r'workspace-bookings', WorkspaceBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calendar/', CalendarView.as_view(), name='booking-calendar'), 
]