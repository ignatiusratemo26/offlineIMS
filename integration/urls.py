from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabIntegrationViewSet, SharedResourceViewSet, SyncLogViewSet, DataSyncQueueViewSet

router = DefaultRouter()
router.register(r'lab-integrations', LabIntegrationViewSet)
router.register(r'shared-resources', SharedResourceViewSet)
router.register(r'sync-logs', SyncLogViewSet)
router.register(r'data-sync-queues', DataSyncQueueViewSet)

urlpatterns = [
    path('', include(router.urls)),
]