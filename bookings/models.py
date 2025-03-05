from django.db import models
from django.conf import settings
from inventory.models import Equipment

class Workspace(models.Model):
    LAB_CHOICES = [
        ('IVE', 'IvE Design Studio'),
        ('CEZERI', 'Cezeri Lab'),
        ('MEDTECH', 'MedTech Lab'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=1)
    lab = models.CharField(max_length=20, choices=LAB_CHOICES)
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='workspaces/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_lab_display()}"

class BookingSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        unique_together = ('date', 'start_time', 'end_time')
    
    def __str__(self):
        return f"{self.date} ({self.start_time} - {self.end_time})"

class EquipmentBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='equipment_bookings')
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE, related_name='equipment_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    purpose = models.TextField()
    project_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_equipment_bookings'
    )
    
    class Meta:
        unique_together = ('equipment', 'slot')
    
    def __str__(self):
        return f"{self.equipment.name} - {self.user.username} - {self.slot}"

class WorkspaceBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspace_bookings')
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE, related_name='workspace_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    purpose = models.TextField()
    project_name = models.CharField(max_length=200, blank=True, null=True)
    participants_count = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_workspace_bookings'
    )
    
    class Meta:
        unique_together = ('workspace', 'slot')
    
    def __str__(self):
        return f"{self.workspace.name} - {self.user.username} - {self.slot}"