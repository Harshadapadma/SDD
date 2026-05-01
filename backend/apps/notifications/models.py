from django.db import models
from apps.users.models import User


class NotificationType(models.TextChoices):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255, default="")
    message = models.TextField(default="")

    type = models.CharField(
        max_length=10,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.public_id} - {self.title}"