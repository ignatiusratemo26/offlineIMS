from django.contrib import admin
from .models import Category, Equipment, MaintenanceRecord, EquipmentUsageLog, EquipmentTransfer

admin.site.register(Category)
admin.site.register(Equipment)
admin.site.register(MaintenanceRecord)
admin.site.register(EquipmentUsageLog)
admin.site.register(EquipmentTransfer)