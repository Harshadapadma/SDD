from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


# -------------------------------
# List Notifications
# -------------------------------
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')

        paginator = NotificationPagination()
        paginated = paginator.paginate_queryset(notifications, request)

        serializer = NotificationSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


# -------------------------------
# Mark Notification as Read
# -------------------------------
class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        # Use update() to avoid fetching the full object — single UPDATE query
        updated = Notification.objects.filter(
            id=notification_id,
            user=request.user
        ).update(is_read=True)

        if not updated:
            return Response({"error": "Not found"}, status=404)

        return Response({"message": "Marked as read"})