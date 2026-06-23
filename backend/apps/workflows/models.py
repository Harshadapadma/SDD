from django.db import models
from apps.users.models import User
from apps.records.models import Record


class DeleteRequestStatus(models.TextChoices):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeleteRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delete_requests")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_delete_requests"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AccessRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="access_requests")
    requested_access = models.CharField(max_length=10, default="EDIT")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_access_requests"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RoleChangeRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_change_requests")
    requested_role = models.CharField(max_length=20)
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_role_requests"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)