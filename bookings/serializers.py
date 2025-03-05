from rest_framework import serializers
from .models import Workspace, BookingSlot, EquipmentBooking, WorkspaceBooking
from inventory.serializers import EquipmentSerializer
from users.serializers import UserUpdateSerializer

class BookingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSlot
        fields = '__all__'

class WorkspaceSerializer(serializers.ModelSerializer):
    lab_display = serializers.CharField(source='get_lab_display', read_only=True)
    
    class Meta:
        model = Workspace
        fields = '__all__'

class EquipmentBookingSerializer(serializers.ModelSerializer):
    equipment_details = EquipmentSerializer(source='equipment', read_only=True)
    user_details = UserUpdateSerializer(source='user', read_only=True)
    slot_details = BookingSlotSerializer(source='slot', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_details = UserUpdateSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = EquipmentBooking
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'status', 'approved_by')

class EquipmentBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBooking
        fields = ('equipment', 'slot', 'purpose', 'project_name', 'notes')
    
    def validate(self, data):
        # Check if equipment is available
        equipment = data['equipment']
        if equipment.status not in ['AVAILABLE', 'IN_USE']:
            raise serializers.ValidationError({
                "equipment": f"Equipment is not available for booking. Current status: {equipment.get_status_display()}"
            })
        
        # Check if slot is already booked for this equipment
        slot = data['slot']
        if EquipmentBooking.objects.filter(equipment=equipment, slot=slot).exists():
            raise serializers.ValidationError({
                "slot": "This time slot is already booked for this equipment."
            })
        
        return data

class WorkspaceBookingSerializer(serializers.ModelSerializer):
    workspace_details = WorkspaceSerializer(source='workspace', read_only=True)
    user_details = UserUpdateSerializer(source='user', read_only=True)
    slot_details = BookingSlotSerializer(source='slot', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_details = UserUpdateSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = WorkspaceBooking
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'status', 'approved_by')

class WorkspaceBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceBooking
        fields = ('workspace', 'slot', 'purpose', 'project_name', 'participants_count', 'notes')
    
    def validate(self, data):
        # Check if workspace has enough capacity
        workspace = data['workspace']
        participants_count = data['participants_count']
        
        if participants_count > workspace.capacity:
            raise serializers.ValidationError({
                "participants_count": f"The workspace capacity ({workspace.capacity}) is less than the number of participants ({participants_count})."
            })
        
        # Check if slot is already booked for this workspace
        slot = data['slot']
        if WorkspaceBooking.objects.filter(workspace=workspace, slot=slot).exists():
            raise serializers.ValidationError({
                "slot": "This time slot is already booked for this workspace."
            })
        
        return data