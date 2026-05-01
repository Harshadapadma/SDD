from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.records.models import Record
from apps.users.models import User
from apps.notifications.models import Notification  # 🔥 added

from .models import DeleteRequest, DeleteRequestStatus, RoleChangeRequest, AccessRequest
from .serializers import DeleteRequestSerializer, RoleChangeRequestSerializer, AccessRequestSerializer


# -------------------------------
# Request Delete
# -------------------------------
class RequestDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        try:
            record = Record.objects.get(public_id=record_id)
        except Record.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        delete_request = DeleteRequest.objects.create(
            record=record,
            requested_by=request.user
        )

        # 🔥 NOTIFY ADMINS
        admins = User.objects.filter(role="ADMIN")
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Delete Request",
                message=f"{request.user.public_id} requested deletion of {record.public_id}",
                type="WARNING"
            )

        return Response({
            "message": "Delete request submitted",
            "request_id": delete_request.id
        })


# -------------------------------
# List Delete Requests (Admin)
# -------------------------------
class DeleteRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        requests = DeleteRequest.objects.all().order_by('-created_at')
        serializer = DeleteRequestSerializer(requests, many=True)

        return Response(serializer.data)


# -------------------------------
# Approve / Reject Delete Request
# -------------------------------
class ReviewDeleteRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        # 🔐 Only admin allowed
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            delete_request = DeleteRequest.objects.get(id=request_id)
        except DeleteRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        # 🚨 Prevent re-processing
        if delete_request.status != DeleteRequestStatus.PENDING:
            return Response(
                {"error": "Request already processed"},
                status=400
            )

        # ✅ Handle actions
        if action == "APPROVE":
            delete_request.status = DeleteRequestStatus.APPROVED
            delete_request.record.delete()

        elif action == "REJECT":
            delete_request.status = DeleteRequestStatus.REJECTED

        else:
            return Response({"error": "Invalid action"}, status=400)

        delete_request.reviewed_by = request.user
        delete_request.save()

        # 🔥 NOTIFY USER (who requested delete)
        Notification.objects.create(
            user=delete_request.requested_by,
            title="Delete Request Update",
            message=f"Your delete request has been {delete_request.status.lower()}",
            type="INFO"
        )

        return Response({
            "message": f"Request {action.lower()}d successfully"
        })

# -------------------------------
# Request Role Change
# -------------------------------
class RequestRoleChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        requested_role = request.data.get("role")
        if requested_role not in ["COLLABORATOR", "VIEWER"]:
            return Response({"error": "Invalid role requested. Only COLLABORATOR or VIEWER can be requested."}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate pending
        if RoleChangeRequest.objects.filter(user=request.user, status=DeleteRequestStatus.PENDING).exists():
            return Response({"error": "You already have a pending role change request"}, status=400)

        role_request = RoleChangeRequest.objects.create(
            user=request.user,
            requested_role=requested_role
        )

        # Notify admins
        admins = User.objects.filter(role="ADMIN")
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Role Change Request",
                message=f"{request.user.name} requested to become {requested_role}",
                type="INFO"
            )

        return Response({
            "message": "Role change request submitted",
            "request_id": role_request.id
        })

# -------------------------------
# List Role Change Requests (Admin)
# -------------------------------
class RoleChangeRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        requests = RoleChangeRequest.objects.all().order_by('-created_at')
        serializer = RoleChangeRequestSerializer(requests, many=True)

        return Response(serializer.data)

# -------------------------------
# Approve / Reject Role Change Request
# -------------------------------
class ReviewRoleChangeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            role_request = RoleChangeRequest.objects.get(id=request_id)
        except RoleChangeRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        if role_request.status != DeleteRequestStatus.PENDING:
            return Response({"error": "Request already processed"}, status=400)

        if action == "APPROVE":
            role_request.status = DeleteRequestStatus.APPROVED
            role_request.user.role = role_request.requested_role
            role_request.user.save()
        elif action == "REJECT":
            role_request.status = DeleteRequestStatus.REJECTED
        else:
            return Response({"error": "Invalid action"}, status=400)

        role_request.reviewed_by = request.user
        role_request.save()

        Notification.objects.create(
            user=role_request.user,
            title="Role Change Update",
            message=f"Your request to become {role_request.requested_role} was {role_request.status.lower()}",
            type="INFO"
        )

        return Response({"message": f"Request {action.lower()}d successfully"})


# -------------------------------
# List User's Own Requests
# -------------------------------
class UserRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get all 3 types
        deletes = DeleteRequest.objects.filter(requested_by=user).order_by('-created_at')
        roles = RoleChangeRequest.objects.filter(user=user).order_by('-created_at')
        access = AccessRequest.objects.filter(user=user).order_by('-created_at')
        
        return Response({
            "delete_requests": DeleteRequestSerializer(deletes, many=True).data,
            "role_requests": RoleChangeRequestSerializer(roles, many=True).data,
            "access_requests": AccessRequestSerializer(access, many=True).data
        })

# -------------------------------
# Request Access Upgrade
# -------------------------------
class RequestAccessUpgradeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        try:
            record = Record.objects.get(public_id=record_id)
        except Record.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        # Prevent duplicate pending
        if AccessRequest.objects.filter(user=request.user, record=record, status=DeleteRequestStatus.PENDING).exists():
            return Response({"error": "You already have a pending access request for this record"}, status=400)

        access_request = AccessRequest.objects.create(
            user=request.user,
            record=record,
            requested_access="EDIT"
        )

        # Notify admins
        admins = User.objects.filter(role="ADMIN")
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Access Upgrade Request",
                message=f"{request.user.name} requested EDIT access for {record.public_id}",
                type="INFO"
            )

        return Response({
            "message": "Access upgrade request submitted",
            "request_id": access_request.id
        })

# -------------------------------
# List Access Requests (Admin)
# -------------------------------
class AccessRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        requests = AccessRequest.objects.all().order_by('-created_at')
        serializer = AccessRequestSerializer(requests, many=True)

        return Response(serializer.data)

# -------------------------------
# Approve / Reject Access Request
# -------------------------------
class ReviewAccessRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            access_request = AccessRequest.objects.get(id=request_id)
        except AccessRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        if access_request.status != DeleteRequestStatus.PENDING:
            return Response({"error": "Request already processed"}, status=400)

        if action == "APPROVE":
            access_request.status = DeleteRequestStatus.APPROVED
            
            # Update or create RecordAccess
            from apps.records.models import RecordAccess
            access_obj, created = RecordAccess.objects.get_or_create(
                user=access_request.user,
                record=access_request.record,
                defaults={'assigned_by': request.user, 'access_type': access_request.requested_access}
            )
            if not created:
                access_obj.access_type = access_request.requested_access
                access_obj.save()

        elif action == "REJECT":
            access_request.status = DeleteRequestStatus.REJECTED
        else:
            return Response({"error": "Invalid action"}, status=400)

        access_request.reviewed_by = request.user
        access_request.save()

        Notification.objects.create(
            user=access_request.user,
            title="Access Request Update",
            message=f"Your request for {access_request.requested_access} access to {access_request.record.public_id} was {access_request.status.lower()}",
            type="INFO"
        )

        return Response({"message": f"Request {action.lower()}d successfully"})