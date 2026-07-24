from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.records.models import Record
from apps.users.models import User
from apps.notifications.models import Notification  # 🔥 added

from .models import DeleteRequest, DeleteRequestStatus, RoleChangeRequest, AccessRequest, CreationRequest, EditRequest, ClarificationMessage
from .serializers import DeleteRequestSerializer, RoleChangeRequestSerializer, AccessRequestSerializer, CreationRequestSerializer, EditRequestSerializer, CreationAuditSerializer, EditAuditSerializer, DeleteAuditSerializer, ClarificationMessageSerializer



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

        if record.status != 'APPROVED':
            return Response(
                {"error": "Cannot request deletion of an unapproved record"},
                status=status.HTTP_400_BAD_REQUEST
            )

        delete_request = DeleteRequest.objects.create(
            record=record,
            requested_by=request.user
        )

        # 🔥 NOTIFY COMPLIANCE OFFICERS
        officers = User.objects.filter(role="COMPLIANCE_OFFICER")
        for officer in officers:
            Notification.objects.create(
                user=officer,
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
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        requests = DeleteRequest.objects.all().order_by('-created_at')
        serializer = DeleteRequestSerializer(requests, many=True)

        return Response(serializer.data)


# -------------------------------
# Approve / Reject Delete Request
# -------------------------------
class ReviewDeleteRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        # 🔐 Only Compliance Officer allowed
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

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
        elif action == "REJECT":
            delete_request.status = DeleteRequestStatus.REJECTED
        else:
            return Response({"error": "Invalid action"}, status=400)

        delete_request.reviewed_by = request.user

        # Capture references before potential deletion wipes them
        record_to_delete = delete_request.record if action == "APPROVE" else None
        record_id_label = record_to_delete.public_id if record_to_delete else "the record"
        requester = delete_request.requested_by

        delete_request.save()

        # 🔥 NOTIFY USER (who requested delete)
        Notification.objects.create(
            user=requester,
            title="Delete Request Update",
            message=f"Your delete request for {record_id_label} has been {delete_request.status.lower()}",
            type="INFO"
        )

        if record_to_delete:
            record_to_delete.delete()

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

        # Notify Compliance Officers
        officers = User.objects.filter(role="COMPLIANCE_OFFICER")
        for officer in officers:
            Notification.objects.create(
                user=officer,
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
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        requests = RoleChangeRequest.objects.all().order_by('-created_at')
        serializer = RoleChangeRequestSerializer(requests, many=True)

        return Response(serializer.data)

# -------------------------------
# Approve / Reject Role Change Request
# -------------------------------
class ReviewRoleChangeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

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

            # 🔥 If role changed to VIEWER, downgrade all EDIT accesses to VIEW
            if role_request.requested_role == "VIEWER":
                from apps.records.models import RecordAccess
                RecordAccess.objects.filter(user=role_request.user, access_type="EDIT").update(access_type="VIEW")
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
        
        # Get all types
        deletes = DeleteRequest.objects.filter(requested_by=user).order_by('-created_at')
        roles = RoleChangeRequest.objects.filter(user=user).order_by('-created_at')
        access = AccessRequest.objects.filter(user=user).order_by('-created_at')
        creations = CreationRequest.objects.filter(requested_by=user).order_by('-created_at')
        edits = EditRequest.objects.filter(requested_by=user).order_by('-created_at')
        
        return Response({
            "delete_requests": DeleteRequestSerializer(deletes, many=True).data,
            "role_requests": RoleChangeRequestSerializer(roles, many=True).data,
            "access_requests": AccessRequestSerializer(access, many=True).data,
            "creation_requests": CreationRequestSerializer(creations, many=True).data,
            "edit_requests": EditRequestSerializer(edits, many=True).data
        })


# -------------------------------
# Pending Request Count (for Red Dot indicator)
# -------------------------------
class PendingRequestCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role in ["COMPLIANCE_OFFICER", "ADMIN"]:
            del_count = DeleteRequest.objects.filter(status='PENDING').count()
            create_count = CreationRequest.objects.filter(status='PENDING').count()
            edit_count = EditRequest.objects.filter(status='PENDING').count()
            role_count = RoleChangeRequest.objects.filter(status='PENDING').count()
            access_count = AccessRequest.objects.filter(status='PENDING').count()
            unread_clarifications = ClarificationMessage.objects.exclude(sender__role__in=['COMPLIANCE_OFFICER', 'ADMIN']).filter(is_read=False).count()
        else:
            del_count = DeleteRequest.objects.filter(requested_by=user, status='PENDING').count()
            create_count = CreationRequest.objects.filter(requested_by=user, status='PENDING').count()
            edit_count = EditRequest.objects.filter(requested_by=user, status='PENDING').count()
            role_count = RoleChangeRequest.objects.filter(user=user, status='PENDING').count()
            access_count = AccessRequest.objects.filter(user=user, status='PENDING').count()
            unread_clarifications = ClarificationMessage.objects.filter(creation_request__requested_by=user, is_read=False).exclude(sender=user).count()

        total_pending = del_count + create_count + edit_count + role_count + access_count
        return Response({
            "pending_count": total_pending,
            "has_pending": total_pending > 0,
            "unread_clarifications_count": unread_clarifications,
            "has_unread_clarifications": unread_clarifications > 0
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

        if request.user.role == "VIEWER":
            return Response(
                {"error": "Viewers cannot request edit access. To get full edit access, the user has to be a Collaborator."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if record.status != 'APPROVED':
            return Response(
                {"error": "Cannot request access upgrade for an unapproved record"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent duplicate pending
        if AccessRequest.objects.filter(user=request.user, record=record, status=DeleteRequestStatus.PENDING).exists():
            return Response({"error": "You already have a pending access request for this record"}, status=400)

        access_request = AccessRequest.objects.create(
            user=request.user,
            record=record,
            requested_access="EDIT"
        )

        # Notify Compliance Officers
        officers = User.objects.filter(role="COMPLIANCE_OFFICER")
        for officer in officers:
            Notification.objects.create(
                user=officer,
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
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        requests = AccessRequest.objects.all().order_by('-created_at')
        serializer = AccessRequestSerializer(requests, many=True)

        return Response(serializer.data)

# -------------------------------
# Approve / Reject Access Request
# -------------------------------
class ReviewAccessRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            access_request = AccessRequest.objects.get(id=request_id)
        except AccessRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        if access_request.status != DeleteRequestStatus.PENDING:
            return Response({"error": "Request already processed"}, status=400)

        if action == "APPROVE":
            if access_request.user.role == "VIEWER" and access_request.requested_access == "EDIT":
                return Response(
                    {"error": "Cannot grant edit access to a Viewer. To get full edit access, the user has to be a Collaborator."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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


# -------------------------------
# List Creation Requests (Compliance Officer)
# -------------------------------
class CreationRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        requests = CreationRequest.objects.all().order_by('-created_at')
        serializer = CreationRequestSerializer(requests, many=True)
        return Response(serializer.data)


# -------------------------------
# Approve / Reject Creation Request (Compliance Officer)
# -------------------------------
class ReviewCreationRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            creation_request = CreationRequest.objects.get(id=request_id)
        except CreationRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        if creation_request.status != DeleteRequestStatus.PENDING:
            return Response({"error": "Request already processed"}, status=400)

        if action == "APPROVE":
            creation_request.status = DeleteRequestStatus.APPROVED
            if creation_request.record:
                creation_request.record.status = "APPROVED"
                creation_request.record.save()
        elif action == "REJECT":
            creation_request.status = DeleteRequestStatus.REJECTED
            if creation_request.record:
                creation_request.record.delete()
        else:
            return Response({"error": "Invalid action"}, status=400)

        creation_request.reviewed_by = request.user
        creation_request.save()

        # Notify requester
        Notification.objects.create(
            user=creation_request.requested_by,
            title="Record Creation Request Update",
            message=f"Your request to create a record has been {action.lower()}d",
            type="INFO"
        )

        return Response({"message": f"Request {action.lower()}d successfully"})


# -------------------------------
# List Edit Requests (Compliance Officer)
# -------------------------------
class EditRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        requests = EditRequest.objects.all().order_by('-created_at')
        serializer = EditRequestSerializer(requests, many=True)
        return Response(serializer.data)


# -------------------------------
# Approve / Reject Edit Request (Compliance Officer)
# -------------------------------
class ReviewEditRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Only Compliance Officer"}, status=403)

        action = request.data.get("action", "").upper()

        try:
            edit_request = EditRequest.objects.get(id=request_id)
        except EditRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        if edit_request.status != DeleteRequestStatus.PENDING:
            return Response({"error": "Request already processed"}, status=400)

        if action == "APPROVE":
            edit_request.status = DeleteRequestStatus.APPROVED
            if edit_request.record:
                from apps.records.serializers import RecordCreateSerializer
                serializer = RecordCreateSerializer(
                    edit_request.record,
                    data=edit_request.proposed_data,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save(updated_by=edit_request.requested_by)
        elif action == "REJECT":
            edit_request.status = DeleteRequestStatus.REJECTED
        else:
            return Response({"error": "Invalid action"}, status=400)

        edit_request.reviewed_by = request.user
        edit_request.save()

        # Notify requester
        Notification.objects.create(
            user=edit_request.requested_by,
            title="Record Edit Request Update",
            message=f"Your request to edit record {edit_request.record.public_id if edit_request.record else ''} has been {action.lower()}d",
            type="INFO"
        )

        return Response({"message": f"Request {action.lower()}d successfully"})


# -------------------------------
# Audit Log View
# -------------------------------
class AuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "COMPLIANCE_OFFICER":
            return Response({"error": "Permission denied"}, status=403)

        creations = CreationRequest.objects.filter(status='APPROVED').order_by('-updated_at')
        editions = EditRequest.objects.filter(status='APPROVED').order_by('-updated_at')
        deletions = DeleteRequest.objects.filter(status='APPROVED').order_by('-updated_at')

        return Response({
            "creations": CreationAuditSerializer(creations, many=True).data,
            "editions": EditAuditSerializer(editions, many=True).data,
            "deletions": DeleteAuditSerializer(deletions, many=True).data
        })


# -------------------------------
# Clarifications views
# -------------------------------
class CreationRequestClarificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        try:
            req = CreationRequest.objects.get(id=request_id)
        except CreationRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        if request.user.role != "COMPLIANCE_OFFICER" and req.requested_by != request.user:
            return Response({"error": "Permission denied"}, status=403)

        # Mark messages sent by the other party as read
        if request.user.role in ["COMPLIANCE_OFFICER", "ADMIN"]:
            req.clarification_messages.exclude(sender__role__in=["COMPLIANCE_OFFICER", "ADMIN"]).filter(is_read=False).update(is_read=True)
        else:
            req.clarification_messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

        messages = req.clarification_messages.all().order_by('created_at')
        serializer = ClarificationMessageSerializer(messages, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, request_id):
        try:
            req = CreationRequest.objects.get(id=request_id)
        except CreationRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        if request.user.role != "COMPLIANCE_OFFICER" and req.requested_by != request.user:
            return Response({"error": "Permission denied"}, status=403)

        msg_text = request.data.get("message", "").strip()
        if not msg_text:
            return Response({"error": "Message cannot be empty"}, status=400)

        message = ClarificationMessage.objects.create(
            creation_request=req,
            sender=request.user,
            message=msg_text,
            is_read=False
        )

        if request.user.role == "COMPLIANCE_OFFICER":
            Notification.objects.create(
                user=req.requested_by,
                title="Clarification Requested",
                message=f"{request.user.name} requested clarification on record creation #{req.id}: {msg_text[:60]}...",
                type="WARNING"
            )
        else:
            officers = User.objects.filter(role="COMPLIANCE_OFFICER")
            for officer in officers:
                Notification.objects.create(
                    user=officer,
                    title="Clarification Reply",
                    message=f"{request.user.name} replied on record creation #{req.id}: {msg_text[:60]}...",
                    type="INFO"
                )

        serializer = ClarificationMessageSerializer(message, context={"request": request})
        return Response(serializer.data, status=201)


class MyClarificationsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "COMPLIANCE_OFFICER":
            reqs = CreationRequest.objects.filter(clarification_messages__isnull=False).distinct().order_by('-updated_at')
        else:
            reqs = CreationRequest.objects.filter(requested_by=user, clarification_messages__isnull=False).distinct().order_by('-updated_at')

        serializer = CreationRequestSerializer(reqs, many=True, context={"request": request})
        return Response(serializer.data)