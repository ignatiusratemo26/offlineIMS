from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    LAB_CHOICES = [
        ('IVE', 'IvE Design Studio'),
        ('CEZERI', 'Cezeri Lab'),
        ('MEDTECH', 'MedTech Lab'),
    ]
    
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('TECHNICIAN', 'Technician'),
        ('STUDENT', 'Student'),
        ('LAB_MANAGER', 'Lab Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    lab = models.CharField(max_length=20, choices=LAB_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    @property
    def is_technician(self):
        return self.role == 'TECHNICIAN'
    
    @property
    def is_student(self):
        return self.role == 'STUDENT'
    
    @property
    def is_lab_manager(self):
        return self.role == 'LAB_MANAGER'