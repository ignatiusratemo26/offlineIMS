from rest_framework import serializers
from .models import Category, Equipment, MaintenanceRecord, EquipmentUsageLog, EquipmentTransfer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'
    
    def get_performed_by_name(self, obj):
        return obj.performed_by.get_full_name() if obj.performed_by else None

class EquipmentUsageLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentUsageLog
        fields = '__all__'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()

class EquipmentTransferSerializer(serializers.ModelSerializer):
    transferred_by_name = serializers.SerializerMethodField()
    equipment_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentTransfer
        fields = '__all__'
    
    def get_transferred_by_name(self, obj):
        return obj.transferred_by.get_full_name()
    
    def get_equipment_name(self, obj):
        return obj.equipment.name

class EquipmentSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipment
        fields = '__all__'
    
    def get_category_name(self, obj):
        return obj.category.name

class EquipmentDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    usage_logs = EquipmentUsageLogSerializer(many=True, read_only=True)
    transfers = EquipmentTransferSerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipment
        fields = '__all__'