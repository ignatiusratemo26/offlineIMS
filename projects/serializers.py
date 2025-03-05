from rest_framework import serializers
from .models import Project, ProjectDocument, ProjectTask, ProjectResource
from django.contrib.auth import get_user_model
from inventory.serializers import EquipmentSerializer

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectDocument
        fields = '__all__'
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name()
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

class ProjectTaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectTask
        fields = '__all__'
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name()
        return None

class ProjectResourceSerializer(serializers.ModelSerializer):
    equipment_details = serializers.SerializerMethodField()
    allocated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectResource
        fields = '__all__'
    
    def get_equipment_details(self, obj):
        return {
            'id': obj.equipment.id,
            'name': obj.equipment.name,
            'serial_number': obj.equipment.serial_number,
            'status': obj.equipment.status
        }
    
    def get_allocated_by_name(self, obj):
        return obj.allocated_by.get_full_name()

class ProjectSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()
    
    def get_team_count(self, obj):
        return obj.team_members.count()

class ProjectDetailSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)
    team_members = UserMiniSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    tasks = ProjectTaskSerializer(many=True, read_only=True)
    resources = ProjectResourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'