from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Project, ProjectDocument, ProjectTask, ProjectResource
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer, ProjectDocumentSerializer, 
    ProjectTaskSerializer, ProjectResourceSerializer
)
from users.permissions import IsAdminUser, IsLabManagerUser
from inventory.models import Equipment

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'status']
    ordering_fields = ['title', 'start_date', 'end_date', 'status', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.all()
        
        # If not admin or lab manager, show only projects user is part of or created
        if not (user.is_admin or user.is_lab_manager):
            queryset = queryset.filter(
                Q(created_by=user) | Q(team_members=user)
            ).distinct()
        
        # Filter by lab if specified
        lab = self.request.query_params.get('lab')
        if lab:
            queryset = queryset.filter(lab=lab)
        
        # Filter by status if specified
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def team_members(self, request, pk=None):
        project = self.get_object()
        
        # Get team members
        members = project.team_members.all()
        
        # Import User model and serializer
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from users.serializers import UserSerializer
        
        # Serialize the team members
        serializer = UserSerializer(members, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_team_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            project.team_members.add(user)
            return Response({"message": f"User {user.username} added to project team"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_team_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            project.team_members.remove(user)
            return Response({"message": f"User {user.username} removed from project team"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['put'])
    def update_team_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not role:
            return Response({"error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # First check if user is a team member
            if user not in project.team_members.all():
                return Response({"error": "User is not a member of this project"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the role (this depends on how your ProjectMember model is structured)
            from .models import ProjectMember
            try:
                project_member = ProjectMember.objects.get(project=project, user=user)
                project_member.role = role
                project_member.save()
                return Response({
                    "message": f"Role updated for user {user.username}",
                    "user_id": user.id,
                    "role": role
                })
            except ProjectMember.DoesNotExist:
                # If using a ManyToMany relationship directly without a through model
                # You might need another approach depending on your model structure
                return Response({"error": "Project member relationship not found"}, status=status.HTTP_404_NOT_FOUND)
                
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        project = self.get_object()
        
        # Get documents for this project
        documents = ProjectDocument.objects.filter(project=project)
        
        # Serialize the documents
        serializer = ProjectDocumentSerializer(documents, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        project = self.get_object()
        
        # Calculate project statistics
        total_documents = project.documents.count()
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='COMPLETED').count()
        
        # Task completion percentage
        task_completion_percentage = 0
        if total_tasks > 0:
            task_completion_percentage = (completed_tasks / total_tasks) * 100
        
        # Get team size
        team_size = project.team_members.count() + 1  # Including project creator
        
        # Get resource utilization
        resource_count = project.resources.count()
        
        # Calculate days since project start
        days_active = 0
        if project.start_date:
            start_date = project.start_date
            today = timezone.now().date()
            days_active = (today - start_date).days
        
        # Calculate days remaining
        days_remaining = None
        if project.end_date:
            end_date = project.end_date
            today = timezone.now().date()
            days_remaining = (end_date - today).days
        
        # Return statistics object
        statistics = {
            'project_id': project.id,
            'project_title': project.title,
            'status': project.status,
            'days_active': days_active,
            'days_remaining': days_remaining,
            'team_size': team_size,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_percentage': task_completion_percentage,
            'total_documents': total_documents,
            'resource_count': resource_count,
            'created_by': {
                'id': project.created_by.id,
                'name': project.created_by.get_full_name() or project.created_by.username
            },
            'lab': project.lab
        }
        
        return Response(statistics)

class ProjectDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'document_type', 'description']
    ordering_fields = ['title', 'document_type', 'uploaded_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Get projects the user has access to
        if user.is_admin or user.is_lab_manager:
            user_projects = Project.objects.all()
        else:
            user_projects = Project.objects.filter(
                Q(created_by=user) | Q(team_members=user)
            ).distinct()
        
        # Return documents for those projects
        queryset = ProjectDocument.objects.filter(project__in=user_projects)
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project__id=project_id)
            
        # Filter by document type if specified
        doc_type = self.request.query_params.get('document_type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class ProjectTaskViewSet(viewsets.ModelViewSet):
    queryset = ProjectTask.objects.all()
    serializer_class = ProjectTaskSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'status']
    ordering_fields = ['title', 'status', 'due_date', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Get projects the user has access to
        if user.is_admin or user.is_lab_manager:
            user_projects = Project.objects.all()
        else:
            user_projects = Project.objects.filter(
                Q(created_by=user) | Q(team_members=user)
            ).distinct()
        
        # Return tasks for those projects
        queryset = ProjectTask.objects.filter(project__in=user_projects)
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project__id=project_id)
            
        # Filter by status if specified
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by assigned user if specified
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to__id=assigned_to)
            
        # Filter by due date
        due_date = self.request.query_params.get('due_date')
        if due_date:
            queryset = queryset.filter(due_date=due_date)
            
        # Filter overdue tasks
        overdue = self.request.query_params.get('overdue')
        if overdue is not None:
            overdue = overdue.lower() == 'true'
            if overdue:
                queryset = queryset.filter(
                    due_date__lt=timezone.now().date(),
                    status__in=['TODO', 'IN_PROGRESS']
                )
                
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ProjectResourceViewSet(viewsets.ModelViewSet):
    queryset = ProjectResource.objects.all()
    serializer_class = ProjectResourceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['project', 'equipment', 'start_date', 'end_date']
    
    def get_queryset(self):
        user = self.request.user
        
        # Get projects the user has access to
        if user.is_admin or user.is_lab_manager:
            user_projects = Project.objects.all()
        else:
            user_projects = Project.objects.filter(
                Q(created_by=user) | Q(team_members=user)
            ).distinct()
        
        # Return resources for those projects
        queryset = ProjectResource.objects.filter(project__in=user_projects)
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project__id=project_id)
            
        # Filter by equipment if specified
        equipment_id = self.request.query_params.get('equipment')
        if equipment_id:
            queryset = queryset.filter(equipment__id=equipment_id)
            
        # Filter by date range
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(
                start_date__lte=date,
                end_date__gte=date
            )
                
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(allocated_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Check if equipment is available for the given time period
        equipment_id = request.data.get('equipment')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        project_id = request.data.get('project')
        
        if not all([equipment_id, start_date, end_date, project_id]):
            return Response(
                {"error": "Equipment, project, start date, and end date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if equipment exists
        try:
            equipment = Equipment.objects.get(id=equipment_id)
        except Equipment.DoesNotExist:
            return Response(
                {"error": "Equipment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if there's a scheduling conflict
        conflicts = ProjectResource.objects.filter(
            equipment=equipment_id,
            # Check for overlapping dates
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(project=project_id)  # Exclude current project
        
        if conflicts.exists():
            return Response(
                {"error": "Equipment is already allocated for this period"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)