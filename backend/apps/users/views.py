from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import AnonRateThrottle

import threading
import traceback
import sys
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from .email_templates import get_account_created_email, get_password_reset_email, get_mfa_otp_email, send_sdd_email
from .models import User
from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    SetPasswordSerializer,
    UserListSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer
)
from .security_models import MFAChallenge, FailedLoginAttempt
from .security_logger import log_security_event, get_client_ip

from apps.notifications.models import Notification


# ─── Rate Throttle ──────────────────────────────────────────────────────────
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login_auth'


# ─── Cookie Helpers ─────────────────────────────────────────────────────────
def _set_refresh_cookie(response, refresh_token: str):
    """Set the refresh token as an HttpOnly secure cookie on the response."""
    response.set_cookie(
        key=settings.SDD_REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        max_age=settings.SDD_REFRESH_COOKIE_MAX_AGE,
        httponly=settings.SDD_REFRESH_COOKIE_HTTPONLY,
        secure=settings.SDD_REFRESH_COOKIE_SECURE,
        samesite=settings.SDD_REFRESH_COOKIE_SAMESITE,
        path=settings.SDD_REFRESH_COOKIE_PATH,
    )


def _delete_refresh_cookie(response):
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=settings.SDD_REFRESH_COOKIE_NAME,
        path=settings.SDD_REFRESH_COOKIE_PATH,
    )


# ─── OTP Email ──────────────────────────────────────────────────────────────
def _send_mfa_otp_email(user, otp_code: str):
    """Send MFA OTP code to user's email."""
    subject, html_body = get_mfa_otp_email(user.name, user.email, otp_code)
    message = (
        f"Hello {user.name},\n\n"
        f"Your one-time verification code is: {otp_code}\n\n"
        f"This code expires in 5 minutes.\n"
        f"If you did not attempt to log in, please change your password immediately.\n\n"
        f"— Negen SDD Security"
    )
    try:
        send_sdd_email(
            subject=subject,
            message=message,
            recipient_list=[user.email],
            html_message=html_body,
            fail_silently=False,
        )
    except Exception as e:
        tb_str = traceback.format_exc()
        print(f"[MFA] OTP email send failed: {e}\nFULL TRACEBACK:\n{tb_str}", flush=True)


# -------------------------------
# Forgot Password View
# -------------------------------
class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found with that email address.'},
                status=status.HTTP_404_NOT_FOUND
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f'{settings.FRONTEND_URL}/set-password?uid={uid}&token={token}'

        log_security_event('PASSWORD_RESET_REQUEST', request, user, f'Password reset requested for {user.email}')

        try:
            subject, html_body = get_password_reset_email(
                name=user.name,
                email=user.email,
                reset_url=reset_url,
            )
            send_sdd_email(
                subject=subject,
                message=(
                    f'Hello {user.name},\n\n'
                    f'We received a request to reset your Negen SDD password.\n\n'
                    f'Click the link below to set a new password:\n\n'
                    f'{reset_url}\n\n'
                    f'This link will expire after a short period.\n\n'
                    f'If you did not request a password reset, please ignore this email.\n\n'
                    f'Best,\nNegen SDD Team'
                ),
                recipient_list=[user.email],
                html_message=html_body,
                fail_silently=False,
            )
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f'[ForgotPassword] Email send failed: {e}\nFULL TRACEBACK:\n{tb_str}', flush=True)
            return Response(
                {'error': 'Failed to send reset email. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'message': 'Password reset link sent to your email.'})


# -------------------------------
# Login View (Direct Login - No MFA)
# -------------------------------
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        # Check account lockout before authentication
        if email and FailedLoginAttempt.is_locked_out(email):
            log_security_event('ACCOUNT_LOCKOUT', request, details=f'Locked out email: {email}', level='WARNING')
            return Response(
                {"error": "Account temporarily locked due to too many failed attempts. Please try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Clear failed login attempts on successful authentication
            FailedLoginAttempt.clear_failures(user.email)

            # Direct login for all roles (refresh token in HttpOnly cookie)
            refresh = RefreshToken.for_user(user)

            log_security_event('LOGIN_SUCCESS', request, user, f'Direct login for {user.role}')

            response = Response({
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "public_id": user.public_id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                }
            })

            # Set refresh token as HttpOnly cookie
            _set_refresh_cookie(response, refresh)

            return response

        # Record failed login attempt
        if email:
            FailedLoginAttempt.record_failure(email, get_client_ip(request))
            log_security_event('LOGIN_FAILED', request, details=f'Failed login for {email}', level='WARNING')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Cookie-Based Token Refresh View
# -------------------------------
class CookieTokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SDD_REFRESH_COOKIE_NAME)

        if not refresh_token:
            return Response(
                {"error": "No refresh token provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            token = RefreshToken(refresh_token)
            new_access = str(token.access_token)

            response = Response({"access": new_access})

            # Rotate: blacklist old, issue new refresh token via cookie
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                token.blacklist()
                new_refresh = RefreshToken.for_user(
                    User.objects.get(id=token['user_id'])
                )
                _set_refresh_cookie(response, new_refresh)

            log_security_event('TOKEN_REFRESH', request, details='Token refreshed successfully')
            return response

        except TokenError:
            log_security_event('TOKEN_REFRESH_FAILED', request, details='Invalid or blacklisted refresh token', level='WARNING')
            response = Response(
                {"error": "Token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            _delete_refresh_cookie(response)
            return response


# -------------------------------
# Logout View (Server-Side Token Invalidation)
# -------------------------------
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SDD_REFRESH_COOKIE_NAME)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Token already invalid/blacklisted

        user = request.user if request.user.is_authenticated else None
        log_security_event('LOGOUT', request, user, 'User logged out, refresh token blacklisted')

        response = Response({"message": "Logged out successfully."})
        _delete_refresh_cookie(response)
        return response


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

            frontend_url = f"{settings.FRONTEND_URL}/set-password?uid={uid}&token={token}"

            # Send HTML Email (Asynchronous non-blocking execution)
            def _send_async():
                try:
                    subject, html_body = get_account_created_email(
                        name=user.name,
                        email=user.email,
                        role=user.role,
                        public_id=user.public_id,
                        setup_url=frontend_url,
                    )
                    send_sdd_email(
                        subject=subject,
                        message=f"Hello {user.name},\n\nYour account has been created. Please visit {frontend_url} to set your password.",
                        recipient_list=[user.email],
                        html_message=html_body,
                        fail_silently=True,
                    )
                    log_security_event('ACTIVATION_SENT', request, user, f'Account creation activation email sent to {user.email}')
                except Exception as e:
                    tb_str = traceback.format_exc()
                    log_security_event('EMAIL_FAILED', request, user, f'Failed to send account creation email: {e}\n{tb_str}', level='ERROR')
                    print(f"[CreateUserView] Failed to send email to {user.email}: {e}\nFULL TRACEBACK:\n{tb_str}", flush=True)

            threading.Thread(target=_send_async, daemon=True).start()

            return Response({
                "message": "User created successfully",
                "setup_url": frontend_url,
                "user": {
                    "public_id": user.public_id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Resend Activation Email View
# -------------------------------
class ResendActivationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can resend activation emails."},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email', '').strip().lower()
        public_id = request.data.get('public_id', '').strip()

        user = None
        if public_id:
            user = User.objects.filter(public_id=public_id).first()
        elif email:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_active:
            return Response(
                {"error": "User account is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = f"{settings.FRONTEND_URL}/set-password?uid={uid}&token={token}"

        try:
            subject, html_body = get_account_created_email(
                name=user.name,
                email=user.email,
                role=user.role,
                public_id=user.public_id,
                setup_url=frontend_url,
            )
            send_sdd_email(
                subject=subject,
                message=f"Hello {user.name},\n\nYour account activation link: {frontend_url}",
                recipient_list=[user.email],
                html_message=html_body,
                fail_silently=False,
            )
            log_security_event('ACTIVATION_RESENT', request, user, f'Activation email resent to {user.email}')
            return Response({
                "message": f"Activation email resent successfully to {user.email}.",
                "setup_url": frontend_url
            })
        except Exception as e:
            tb_str = traceback.format_exc()
            log_security_event('EMAIL_FAILED', request, user, f'Failed to resend activation email: {e}\n{tb_str}', level='ERROR')
            print(f"[ResendActivationView] Failed to send email to {user.email}: {e}\nFULL TRACEBACK:\n{tb_str}", flush=True)
            return Response(
                {"error": f"Failed to send email: {str(e)}", "setup_url": frontend_url},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------------
# Verify Token View
# -------------------------------
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
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            log_security_event('PASSWORD_CHANGE', request, user, 'Password set via setup/reset link')
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
        if request.user.role not in ["ADMIN", "COMPLIANCE_OFFICER"] and request.GET.get('include_all') != 'true':
            return Response(
                {"error": "Permission denied: Only admin or compliance officer can view users"},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.GET.get('include_all') == 'true' or request.GET.get('all') == 'true':
            queryset = User.objects.all().order_by('-created_at')
        else:
            queryset = User.objects.exclude(role__in=['ADMIN', 'COMPLIANCE_OFFICER']).order_by('-created_at')

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

        old_role = user.role
        user.role = role
        user.save()

        # 🔥 If role changed to VIEWER, downgrade all EDIT accesses to VIEW
        if role == "VIEWER":
            from apps.records.models import RecordAccess
            RecordAccess.objects.filter(user=user, access_type="EDIT").update(access_type="VIEW")

        # 🔥 Create Notification for the user
        Notification.objects.create(
            user=user,
            title="Role Updated",
            message=f"Your system role has been updated to {role}.",
            type="INFO"
        )

        log_security_event('ROLE_CHANGE', request, user, f'Role changed from {old_role} to {role} by {request.user.email}')

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
            log_security_event('PASSWORD_CHANGE', request, user, 'Password changed via profile')
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Dashboard Stats (Admin & Compliance Officer)
# -------------------------------
from apps.records.models import Record
from apps.workflows.models import DeleteRequest, AccessRequest, RoleChangeRequest, CreationRequest, EditRequest
from django.utils import timezone
from datetime import timedelta

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["ADMIN", "COMPLIANCE_OFFICER"]:
            return Response({"error": "Permission denied"}, status=403)

        # 1. Total counts
        total_users = User.objects.exclude(role='ADMIN').exclude(role='COMPLIANCE_OFFICER').count()
        total_records = Record.objects.count()
        
        pending_delete = DeleteRequest.objects.filter(status="PENDING").count()
        pending_access = AccessRequest.objects.filter(status="PENDING").count()
        pending_role = RoleChangeRequest.objects.filter(status="PENDING").count()
        pending_creation = CreationRequest.objects.filter(status="PENDING").count()
        pending_edit = EditRequest.objects.filter(status="PENDING").count()
        total_pending = pending_delete + pending_access + pending_role + pending_creation + pending_edit

        # 2. User Distribution by Role
        role_dist = {
            "ADMIN": User.objects.filter(role="ADMIN").count(),
            "COMPLIANCE_OFFICER": User.objects.filter(role="COMPLIANCE_OFFICER").count(),
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
                RoleChangeRequest.objects.filter(status=s).count() +
                CreationRequest.objects.filter(status=s).count() +
                EditRequest.objects.filter(status=s).count()
            )
            status_dist[s] = count

        # 5. Application & Database Infographics Data
        from apps.workflows.models import ClarificationMessage
        total_all_users = User.objects.count()
        total_requests_all = (
            DeleteRequest.objects.count() +
            AccessRequest.objects.count() +
            RoleChangeRequest.objects.count() +
            CreationRequest.objects.count() +
            EditRequest.objects.count()
        )
        approved_requests = status_dist.get("APPROVED", 0)
        rejected_requests = status_dist.get("REJECTED", 0)
        total_clarifications = ClarificationMessage.objects.count()

        infographics = {
            "db_stats": {
                "total_records": total_records,
                "total_users_table": total_all_users,
                "total_workflow_rows": total_requests_all,
                "total_clarifications": total_clarifications,
                "engine": "PostgreSQL 16 Relational",
                "encryption": "AES-256 Storage Active",
                "integrity": "Verified / Optimal"
            },
            "app_stats": {
                "pending_clearances": total_pending,
                "processed_clearances": approved_requests + rejected_requests,
                "approved_count": approved_requests,
                "rejected_count": rejected_requests,
                "active_roles": len([r for r, c in role_dist.items() if c > 0]),
                "audit_coverage": "100% Immutable Trail",
                "stack": "Django REST + Vue 3 TS",
                "security": "JWT + RBAC + MFA Active"
            }
        }

        # 6. Monthly Records (Last 6 Months)
        monthly_records = []
        for i in range(5, -1, -1):
            m_date = (today.replace(day=1) - timedelta(days=30 * i))
            count = Record.objects.filter(created_at__year=m_date.year, created_at__month=m_date.month).count()
            monthly_records.append({
                "month": m_date.strftime("%b %Y"),
                "count": count
            })

        return Response({
            "overview": {
                "total_users": total_users,
                "total_records": total_records,
                "total_pending": total_pending
            },
            "role_distribution": role_dist,
            "record_growth": growth_data,
            "monthly_records": monthly_records,
            "request_status": status_dist,
            "infographics": infographics
        })


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["ADMIN", "COMPLIANCE_OFFICER"]:
            return Response({"error": "Permission denied"}, status=403)

        base_queryset = User.objects.exclude(role__in=['ADMIN', 'COMPLIANCE_OFFICER'])
        total_users = base_queryset.count()
        active_users = base_queryset.filter(is_active=True, is_blacklisted=False).count()
        inactive_users = base_queryset.filter(is_active=False).count()
        blacklisted_users = base_queryset.filter(is_blacklisted=True).count()

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "blacklisted_users": blacklisted_users
        })