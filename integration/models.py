from django.db import models
from django.conf import settings
from django.utils import timezone

class LabIntegration(models.Model):
    LAB_CHOICES = [
        ('IVE', 'IvE Design Studio'),
        ('CEZERI', 'Cezeri Lab'),
        ('MEDTECH', 'MedTech Lab'),
    ]
    
    lab_name = models.CharField(max_length=20, choices=LAB_CHOICES, unique=True)
    ip_address = models.GenericIPAddressField(help_text="IP address of the lab's local server")
    sync_port = models.PositiveIntegerField(default=8000, help_text="Port for syncing data")
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_lab_name_display()} Integration"

class SharedResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('EQUIPMENT', 'Equipment'),
        ('WORKSPACE', 'Workspace'),
    ]
    
    LAB_CHOICES = [
        ('IVE', 'IvE Design Studio'),
        ('CEZERI', 'Cezeri Lab'),
        ('MEDTECH', 'MedTech Lab'),
    ]
    
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    resource_id = models.PositiveIntegerField(help_text="ID of the resource in its original lab")
    resource_name = models.CharField(max_length=200)
    owner_lab = models.CharField(max_length=20, choices=LAB_CHOICES)
    shared_with_lab = models.CharField(max_length=20, choices=LAB_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('resource_type', 'resource_id', 'owner_lab', 'shared_with_lab')
    
    def __str__(self):
        return f"{self.resource_name} shared from {self.owner_lab} to {self.shared_with_lab}"

class SyncLog(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial Success'),
    ]
    
    source_lab = models.CharField(max_length=20, choices=LabIntegration.LAB_CHOICES)
    target_lab = models.CharField(max_length=20, choices=LabIntegration.LAB_CHOICES)
    sync_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    items_synced = models.PositiveIntegerField(default=0)
    items_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sync_logs'
    )
    
    def __str__(self):
        return f"Sync from {self.source_lab} to {self.target_lab} - {self.sync_time}"

class DataSyncQueue(models.Model):
    SYNC_TYPE_CHOICES = [
        ('USER', 'User'),
        ('EQUIPMENT', 'Equipment'),
        ('WORKSPACE', 'Workspace'),
        ('PROJECT', 'Project'),
        ('BOOKING', 'Booking'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    source_lab = models.CharField(max_length=20, choices=LabIntegration.LAB_CHOICES)
    target_lab = models.CharField(max_length=20, choices=LabIntegration.LAB_CHOICES)
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    item_id = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    data_payload = models.JSONField(help_text="JSON data to be synced")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('source_lab', 'sync_type', 'item_id')
    
    def __str__(self):
        return f"{self.sync_type} sync from {self.source_lab} - {self.status}"