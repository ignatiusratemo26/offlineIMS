from rest_framework import serializers
from .models import LabIntegration, SharedResource, SyncLog, DataSyncQueue

class LabIntegrationSerializer(serializers.ModelSerializer):
    lab_name_display = serializers.CharField(source='get_lab_name_display', read_only=True)
    
    class Meta:
        model = LabIntegration
        fields = '__all__'

class SharedResourceSerializer(serializers.ModelSerializer):
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    owner_lab_display = serializers.CharField(source='get_owner_lab_display', read_only=True)
    shared_with_lab_display = serializers.CharField(source='get_shared_with_lab_display', read_only=True)
    
    class Meta:
        model = SharedResource
        fields = '__all__'

class SyncLogSerializer(serializers.ModelSerializer):
    source_lab_display = serializers.CharField(source='get_source_lab_display', read_only=True)
    target_lab_display = serializers.CharField(source='get_target_lab_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    initiated_by_username = serializers.CharField(source='initiated_by.username', read_only=True)
    
    class Meta:
        model = SyncLog
        fields = '__all__'

class DataSyncQueueSerializer(serializers.ModelSerializer):
    source_lab_display = serializers.CharField(source='get_source_lab_display', read_only=True)
    target_lab_display = serializers.CharField(source='get_target_lab_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DataSyncQueue
        fields = '__all__'