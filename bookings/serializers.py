from rest_framework import serializers
from .models import Workspace, Booking, EquipmentBooking
from django.contrib.auth import get_user_model
from projects.serializers import ProjectSerializer
from inventory.serializers import EquipmentSerializer
from django.utils import timezone


User = get_user_model()

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    
    def get_workspace_name(self, obj):
        return f"{obj.workspace.name} ({obj.workspace.get_lab_display()})"
    
    def get_project_title(self, obj):
        if obj.project:
            return obj.project.title
        return None

class BookingDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    workspace = WorkspaceSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'email': obj.user.email
        }
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name()
        return None

class EquipmentBookingSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    equipment_name = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentBooking
        fields = '__all__'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    
    def get_equipment_name(self, obj):
        return obj.equipment.name
    
    def get_project_title(self, obj):
        if obj.project:
            return obj.project.title
        return None
    
    def validate(self, data):
        # Check if the equipment is available
        if data['equipment'].status != 'AVAILABLE':
            raise serializers.ValidationError('Equipment is not available')
        
        # Check if the booking is in the future
        if data['start_time'] < timezone.now():
            raise serializers.ValidationError('Cannot book in the past')
        
        # Check if end time is after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError('End time must be after start time')
        
        # Check for overlapping bookings
        overlapping_bookings = EquipmentBooking.objects.filter(
            equipment=data['equipment'],
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time'],
            status='APPROVED'
        )
        
        if self.instance:
            overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)
        
        if overlapping_bookings:
            raise serializers.ValidationError('Equipment is already booked for this time')
        
        return data