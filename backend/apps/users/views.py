from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from .models import User
from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    SetPasswordSerializer,
    UserListSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer
)

from apps.notifications.models import Notification  # 🔥 added


# -------------------------------
# Login View
# -------------------------------
class LoginView(APIView):
    authentication_classes = []      # ← don't try to validate any token
    permission_classes = [AllowAny]  # ← allow unauthenticated access

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "public_id": user.public_id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                }
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Admin Create User View
# -------------------------------
class CreateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can create users"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # 🔥 NOTIFICATION ADDED HERE
            Notification.objects.create(
                user=user,
                title="Account Created",
                message="Your account has been created. Please set your password.",
                type="INFO"
            )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_url = f"http://localhost:5173/set-password?uid={uid}&token={token}"

            # Send Email
            try:
                send_mail(
                    subject="Welcome to Negen SDD - Set Your Password",
                    message=f"Hello {user.name},\n\nAn account has been created for you on Negen SDD with the role '{user.role}'.\n\nPlease click the link below to set up your password and access your vault:\n\n{frontend_url}\n\nIf you did not request this, please ignore this email.\n\nBest,\nNegen SDD Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")

            return Response({
                "message": "User created successfully",
                "user": {
                    "public_id": user.public_id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Verify Token View
# -------------------------------
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

class VerifySetupTokenView(APIView):
    def get(self, request):
        uidb64 = request.query_params.get('uid')
        token = request.query_params.get('token')

        if not uidb64 or not token:
            return Response({"error": "Missing uid or token"}, status=400)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid user ID"}, status=400)

        if default_token_generator.check_token(user, token):
            return Response({
                "name": user.name,
                "email": user.email,
                "public_id": user.public_id
            })
        
        return Response({"error": "Token is invalid or expired"}, status=400)


# -------------------------------
# Set Password View
# -------------------------------
class SetPasswordView(APIView):
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password set successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Pagination
# -------------------------------
class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# -------------------------------
# List Users
# -------------------------------
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can view users"},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = User.objects.all().order_by('-created_at')

        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(public_id__icontains=search)
            )

        role = request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)

        paginator = UserPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = UserListSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)

# -------------------------------
# Blacklist User
# -------------------------------
class BlacklistUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, public_id):
        if request.user.role != "ADMIN":
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(public_id=public_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        user.is_blacklisted = not user.is_blacklisted
        user.save()

        # 🔥 Create Notification
        status_msg = "blacklisted" if user.is_blacklisted else "unblacklisted"
        Notification.objects.create(
            user=user,
            title="Account Status Updated",
            message=f"Your account has been {status_msg} by the administrator.",
            type="WARNING" if user.is_blacklisted else "SUCCESS"
        )

        return Response({"message": f"User {status_msg}"})

# -------------------------------
# Change Role
# -------------------------------
class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, public_id):
        if request.user.role != "ADMIN":
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(public_id=public_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        role = request.data.get("role")
        if role not in ["COLLABORATOR", "VIEWER"]:
            return Response({"error": "Invalid role or permission denied to set ADMIN"}, status=status.HTTP_400_BAD_REQUEST)
            
        if user.role == "ADMIN":
            return Response({"error": "Cannot change role of an ADMIN user"}, status=status.HTTP_400_BAD_REQUEST)

        user.role = role
        user.save()

        # 🔥 Create Notification for the user
        Notification.objects.create(
            user=user,
            title="Role Updated",
            message=f"Your system role has been updated to {role}.",
            type="INFO"
        )

        return Response({"message": "Role updated successfully"})

# -------------------------------
# Profile View
# -------------------------------
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserListSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserListSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Ping User View
# -------------------------------
class PingUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        if request.user.role != "ADMIN":
            return Response({"error": "Permission denied"}, status=403)
        
        try:
            user = User.objects.get(public_id=public_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        
        Notification.objects.create(
            user=user,
            title="Profile Incomplete",
            message="Administrator reminds you to complete your profile (designation, company, mobile).",
            type="WARNING"
        )
        return Response({"message": "User pinged successfully"})


# -------------------------------
# Change Password View
# -------------------------------
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Dashboard Stats (Admin Only)
# -------------------------------
from apps.records.models import Record
from apps.workflows.models import DeleteRequest, AccessRequest, RoleChangeRequest
from django.utils import timezone
from datetime import timedelta

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"error": "Permission denied"}, status=403)

        # 1. Total counts
        total_users = User.objects.count()
        total_records = Record.objects.count()
        
        pending_delete = DeleteRequest.objects.filter(status="PENDING").count()
        pending_access = AccessRequest.objects.filter(status="PENDING").count()
        pending_role = RoleChangeRequest.objects.filter(status="PENDING").count()
        total_pending = pending_delete + pending_access + pending_role

        # 2. User Distribution by Role
        role_dist = {
            "ADMIN": User.objects.filter(role="ADMIN").count(),
            "COLLABORATOR": User.objects.filter(role="COLLABORATOR").count(),
            "VIEWER": User.objects.filter(role="VIEWER").count(),
        }

        # 3. Record Growth (Last 14 Days)
        today = timezone.now().date()
        growth_data = []
        for i in range(13, -1, -1):
            date = today - timedelta(days=i)
            count = Record.objects.filter(created_at__date=date).count()
            growth_data.append({
                "date": date.strftime("%d %b"),
                "count": count
            })

        # 4. Request Status (Combined)
        all_statuses = ["PENDING", "APPROVED", "REJECTED"]
        status_dist = {}
        for s in all_statuses:
            count = (
                DeleteRequest.objects.filter(status=s).count() +
                AccessRequest.objects.filter(status=s).count() +
                RoleChangeRequest.objects.filter(status=s).count()
            )
            status_dist[s] = count

        return Response({
            "overview": {
                "total_users": total_users,
                "total_records": total_records,
                "total_pending": total_pending
            },
            "role_distribution": role_dist,
            "record_growth": growth_data,
            "request_status": status_dist
        })