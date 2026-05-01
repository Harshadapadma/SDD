from django.urls import path
from .views import (
    RequestDeleteView, DeleteRequestListView, ReviewDeleteRequestView,
    RequestRoleChangeView, RoleChangeRequestListView, ReviewRoleChangeRequestView,
    RequestAccessUpgradeView, AccessRequestListView, ReviewAccessRequestView,
    UserRequestsListView
)

urlpatterns = [
    # User's own requests
    path('my-requests/', UserRequestsListView.as_view()),

    # Delete Requests
    path('request/<str:record_id>/', RequestDeleteView.as_view()),
    path('', DeleteRequestListView.as_view()),
    path('review/<int:request_id>/', ReviewDeleteRequestView.as_view()),
    
    # Role Change Requests
    path('role-change/request/', RequestRoleChangeView.as_view()),
    path('role-change/', RoleChangeRequestListView.as_view()),
    path('role-change/review/<int:request_id>/', ReviewRoleChangeRequestView.as_view()),

    # Access Upgrade Requests
    path('access-upgrade/request/<str:record_id>/', RequestAccessUpgradeView.as_view()),
    path('access-upgrade/', AccessRequestListView.as_view()),
    path('access-upgrade/review/<int:request_id>/', ReviewAccessRequestView.as_view()),
]