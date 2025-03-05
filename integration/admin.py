from django.contrib import admin
from .models import LabIntegration, SharedResource, SyncLog, DataSyncQueue

admin.site.register(LabIntegration)
admin.site.register(SharedResource)
admin.site.register(SyncLog)
admin.site.register(DataSyncQueue)