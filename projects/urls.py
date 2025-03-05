from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ProjectDocumentViewSet, ProjectTaskViewSet, ProjectResourceViewSet
)

router = DefaultRouter()
router.register(r'', ProjectViewSet)
router.register(r'documents', ProjectDocumentViewSet)
router.register(r'tasks', ProjectTaskViewSet)
router.register(r'resources', ProjectResourceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]