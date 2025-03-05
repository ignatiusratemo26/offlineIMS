from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Equipment(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('IN_USE', 'In Use'),
        ('MAINTENANCE', 'Maintenance'),
        ('SHARED', 'Shared with another lab'),
    ]
    
    LAB_CHOICES = [
        ('IVE', 'IvE Design Studio'),
        ('CEZERI', 'Cezeri Lab'),
        ('MEDTECH', 'MedTech Lab'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='equipment')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    lab = models.CharField(max_length=20, choices=LAB_CHOICES)
    location = models.CharField(max_length=100, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    last_maintenance_date = models.DateField(blank=True, null=True)
    next_maintenance_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='equipment/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.serial_number}"

class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_date = models.DateField()
    description = models.TextField()
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='maintenance_performed')
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_date}"

class EquipmentUsageLog(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='usage_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='equipment_used')
    check_out_time = models.DateTimeField()
    check_in_time = models.DateTimeField(blank=True, null=True)
    purpose = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.equipment.name} used by {self.user.username}"

class EquipmentTransfer(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='transfers')
    from_lab = models.CharField(max_length=20, choices=Equipment.LAB_CHOICES)
    to_lab = models.CharField(max_length=20, choices=Equipment.LAB_CHOICES)
    transferred_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers_made')
    transfer_date = models.DateTimeField()
    return_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.equipment.name} transferred from {self.from_lab} to {self.to_lab}"