from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/integration/', include('integration.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)