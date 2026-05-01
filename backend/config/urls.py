from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & Users
    path('api/auth/', include('apps.users.urls')),

    # Records
    path('api/records/', include('apps.records.urls')),

    # Workflows
    path('api/workflows/', include('apps.workflows.urls')),

    # Notifications
    path('api/notifications/', include('apps.notifications.urls')),
]