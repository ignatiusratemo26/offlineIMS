from django.contrib import admin
from .models import Workspace, BookingSlot, EquipmentBooking, WorkspaceBooking

admin.site.register(Workspace)
admin.site.register(BookingSlot)
admin.site.register(EquipmentBooking)
admin.site.register(WorkspaceBooking)