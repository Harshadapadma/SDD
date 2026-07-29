# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from apps.users.models import User
from apps.records.models import Record


class DeleteRequestStatus(models.TextChoices):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeleteRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True, blank=True)
    record_public_id = models.CharField(max_length=50, null=True, blank=True)
    record_name = models.CharField(max_length=255, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delete_requests")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING,
        db_index=True
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

    def save(self, *args, **kwargs):
        if self.record:
            if not self.record_public_id:
                self.record_public_id = self.record.public_id
            if not self.record_name:
                self.record_name = self.record.name
        super().save(*args, **kwargs)

class AccessRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="access_requests")
    requested_access = models.CharField(max_length=10, default="EDIT")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING,
        db_index=True
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
        default=DeleteRequestStatus.PENDING,
        db_index=True
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


class CreationRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True, blank=True, related_name="creation_requests")
    record_public_id = models.CharField(max_length=50, null=True, blank=True)
    record_name = models.CharField(max_length=255, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creation_requests")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_creation_requests"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.record:
            if not self.record_public_id:
                self.record_public_id = self.record.public_id
            if not self.record_name:
                self.record_name = self.record.name
        super().save(*args, **kwargs)


class EditRequest(models.Model):
    record = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True, blank=True, related_name="edit_requests")
    record_public_id = models.CharField(max_length=50, null=True, blank=True)
    record_name = models.CharField(max_length=255, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="edit_requests")
    status = models.CharField(
        max_length=10,
        choices=DeleteRequestStatus.choices,
        default=DeleteRequestStatus.PENDING,
        db_index=True
    )
    proposed_data = models.JSONField()
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_edit_requests"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.record:
            if not self.record_public_id:
                self.record_public_id = self.record.public_id
            if not self.record_name:
                self.record_name = self.record.name
        super().save(*args, **kwargs)


class ClarificationMessage(models.Model):
    creation_request = models.ForeignKey(
        CreationRequest,
        on_delete=models.CASCADE,
        related_name='clarification_messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_clarification_messages'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg from {self.sender.name} on Req #{self.creation_request.id}"