from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserUpdateSerializer, CustomTokenObtainPairSerializer
from .permissions import IsAdminUser, IsSameUserOrAdmin

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return UserSerializer
        return UserUpdateSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSameUserOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_lab_manager:
            # Admins and lab managers can see all users
            return User.objects.all()
        # Others can only see users from their lab
        return User.objects.filter(lab=user.lab)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserUpdateSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def lab_users(self, request):
        lab = request.query_params.get('lab')
        if not lab:
            return Response({"error": "Lab parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        users = User.objects.filter(lab=lab)
        serializer = UserUpdateSerializer(users, many=True)
        return Response(serializer.data)