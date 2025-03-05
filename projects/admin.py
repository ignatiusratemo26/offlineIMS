from django.contrib import admin
from .models import Project, ProjectDocument, ProjectTask, ProjectResource

admin.site.register(Project)
admin.site.register(ProjectDocument)
admin.site.register(ProjectTask)
admin.site.register(ProjectResource)