from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .models import Record, RecordAccess
from .serializers import RecordCreateSerializer, RecordListSerializer, RecordDetailSerializer

from apps.users.models import User
from apps.notifications.models import Notification  # 🔥 added
from apps.workflows.models import DeleteRequest, CreationRequest, EditRequest


# -------------------------------
# Pagination
# -------------------------------
class RecordPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


# -------------------------------
# Create Record
# -------------------------------
class CreateRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ["COLLABORATOR", "COMPLIANCE_OFFICER"]:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RecordCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            record = serializer.save()

            if request.user.role == "COMPLIANCE_OFFICER":
                record.status = 'APPROVED'
                record.save()

                return Response({
                    "message": "Record created successfully",
                    "record_id": record.public_id
                }, status=status.HTTP_201_CREATED)
            else:
                record.status = 'PENDING_CREATION'
                record.save()

                # Create creation request
                CreationRequest.objects.create(
                    record=record,
                    requested_by=request.user
                )

                # Notify Compliance Officers
                officers = User.objects.filter(role="COMPLIANCE_OFFICER")
                for officer in officers:
                    Notification.objects.create(
                        user=officer,
                        title="Record Creation Request",
                        message=f"{request.user.name} requested creation of record {record.public_id}",
                        type="INFO"
                    )

                return Response({
                    "message": "Record creation request submitted for approval",
                    "record_id": record.public_id
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# List Records
# -------------------------------
class RecordListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 🔐 ACCESS CONTROL
        if user.role == "COMPLIANCE_OFFICER":
            queryset = Record.objects.all()
        elif user.role == "ADMIN":
            return Response({"error": "Permission denied. Admins cannot view records."}, status=status.HTTP_403_FORBIDDEN)
        else:
            queryset = Record.objects.filter(
                Q(user_access__user=user, status='APPROVED') |
                Q(created_by=user, status='PENDING_CREATION')
            )

        queryset = queryset.order_by('-created_at')

        # 🔍 Search
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(pan__icontains=search) |
                Q(public_id__icontains=search)
            )

        # 📄 Pagination
        paginator = RecordPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = RecordListSerializer(paginated_queryset, many=True, context={"request": request})

        return paginator.get_paginated_response(serializer.data)


# -------------------------------
# Assign Access to Record
# -------------------------------
class AssignRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ["ADMIN", "COMPLIANCE_OFFICER"]:
            return Response(
                {"error": "Only admin or compliance officer can assign records"},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user_id")
        record_id = request.data.get("record_id")
        access_type = request.data.get("access_type", "VIEW")

        try:
            user = User.objects.get(public_id=user_id)
            record = Record.objects.get(public_id=record_id)
        except:
            return Response(
                {"error": "Invalid user_id or record_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.role == "VIEWER" and access_type == "EDIT":
            return Response(
                {"error": "Full edit access can't be given unless the user is a Collaborator."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if record.status != 'APPROVED':
            return Response(
                {"error": "Cannot assign access to an unapproved record"},
                status=status.HTTP_400_BAD_REQUEST
            )

        access, created = RecordAccess.objects.get_or_create(
            user=user,
            record=record,
            defaults={
                "access_type": access_type,
                "assigned_by": request.user
            }
        )

        if not created:
            access.access_type = access_type
            access.save()

        # 🔥 NOTIFICATION ADDED HERE
        Notification.objects.create(
            user=user,
            title="Record Assigned",
            message=f"You have been assigned record {record.public_id}",
            type="SUCCESS"
        )

        return Response({
            "message": "Record assigned successfully"
        })


# -------------------------------
# Update Record
# -------------------------------
class UpdateRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, record_id):
        try:
            record = Record.objects.get(public_id=record_id)
        except Record.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        user = request.user

        # If it's a pending creation request and the user is the creator, let them update it directly
        if record.status == 'PENDING_CREATION':
            if record.created_by != user:
                return Response(
                    {"error": "Permission denied. Only the creator can edit a pending record."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = RecordCreateSerializer(
                record,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response({
                    "message": "Pending record updated successfully",
                    "record_id": record.public_id
                })
            return Response(serializer.errors, status=400)

        # For approved records, perform normal check and edit request flow
        if record.status != 'APPROVED':
            return Response(
                {"error": "Cannot edit an unapproved record"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔐 ACCESS CONTROL
        if user.role not in ["ADMIN", "COMPLIANCE_OFFICER"]:
            has_access = RecordAccess.objects.filter(
                user=user,
                record=record,
                access_type="EDIT"
            ).exists()

            if not has_access:
                return Response(
                    {"error": "No edit permission"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = RecordCreateSerializer(
            record,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            # Create Edit Request instead of saving directly
            EditRequest.objects.create(
                record=record,
                requested_by=user,
                proposed_data=request.data
            )

            # Notify Compliance Officers
            officers = User.objects.filter(role="COMPLIANCE_OFFICER")
            for officer in officers:
                Notification.objects.create(
                    user=officer,
                    title="Record Edit Request",
                    message=f"{user.name} requested edit of record {record.public_id}",
                    type="WARNING"
                )

            return Response({
                "message": "Record edit request submitted for approval"
            })

        return Response(serializer.errors, status=400)


# -------------------------------
# Delete Record
# -------------------------------
class DeleteRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, record_id):
        try:
            record = Record.objects.get(public_id=record_id)
        except Record.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        if record.status != 'APPROVED':
            return Response(
                {"error": "Cannot request deletion of an unapproved record"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        if user.role not in ["ADMIN", "COLLABORATOR"]:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        if user.role == "COLLABORATOR":
            has_access = RecordAccess.objects.filter(
                user=user,
                record=record,
                access_type="EDIT"
            ).exists()
            if not has_access:
                return Response({"error": "No delete permission"}, status=status.HTTP_403_FORBIDDEN)

        # Create Delete Request
        DeleteRequest.objects.create(record=record, requested_by=user)

        # Notify Compliance Officers
        officers = User.objects.filter(role="COMPLIANCE_OFFICER")
        for officer in officers:
            Notification.objects.create(
                user=officer,
                title="Delete Request",
                message=f"{user.name} requested to delete record {record.public_id}",
                type="WARNING"
            )

        return Response({"message": "Delete request sent to Compliance Officer for approval"}, status=status.HTTP_202_ACCEPTED)


# -------------------------------
# Record Detail (with access list for Admin)
# -------------------------------
class RecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = Record.objects.get(public_id=record_id)
        except Record.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        user = request.user
        
        # 🔐 ACCESS CONTROL
        if user.role == "ADMIN":
            return Response({"error": "Permission denied. Admins cannot view records."}, status=status.HTTP_403_FORBIDDEN)
        elif user.role != "COMPLIANCE_OFFICER":
            if record.status == 'PENDING_CREATION' and record.created_by != user:
                return Response({"error": "Permission denied"}, status=403)
            has_access = RecordAccess.objects.filter(user=user, record=record).exists()
            if not has_access:
                return Response({"error": "Permission denied"}, status=403)

        # Basic record data
        serializer = RecordDetailSerializer(record, context={"request": request})
        data = serializer.data

        # If admin or compliance officer, add access details
        if user.role in ["ADMIN", "COMPLIANCE_OFFICER"]:
            accesses = RecordAccess.objects.filter(record=record)
            access_list = []
            for acc in accesses:
                access_list.append({
                    "user_name": acc.user.name,
                    "user_id": acc.user.public_id,
                    "access_type": acc.access_type,
                    "assigned_at": acc.assigned_at
                })
            data["access_list"] = access_list

        return Response(data)