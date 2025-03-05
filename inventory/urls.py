from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, EquipmentViewSet, MaintenanceRecordViewSet, 
    EquipmentUsageLogViewSet, EquipmentTransferViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'maintenance', MaintenanceRecordViewSet)
router.register(r'usage-logs', EquipmentUsageLogViewSet)
router.register(r'transfers', EquipmentTransferViewSet)

urlpatterns = [
    path('', include(router.urls)),
]