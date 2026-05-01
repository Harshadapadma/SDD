from django.db import models
from django.utils import timezone


# -------------------------------
# Record Model
# -------------------------------
class Record(models.Model):
    """
    Core business entity for Negen Capitals.
    Stores disclosure / sensitive information records.
    """

    # Public ID like: NR-2026-0001
    public_id = models.CharField(max_length=20, unique=True, editable=False)

    # Basic Info
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    employee_code = models.CharField(max_length=50)

    pan = models.CharField(max_length=20)

    source_company = models.CharField(max_length=255)
    info_details = models.TextField()

    info_received_date = models.DateField()

    disclosure_name = models.CharField(max_length=255)
    disclosure_designation = models.CharField(max_length=255)

    # Metadata
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='records_created'
    )

    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records_updated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Generate public_id like NR-2026-0001
        Resets sequence every year
        """
        if not self.public_id:
            current_year = timezone.now().year

            # Get last record for current year
            last_record = Record.objects.filter(
                public_id__startswith=f"NR-{current_year}"
            ).order_by('-id').first()

            if last_record and last_record.public_id:
                last_number = int(last_record.public_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.public_id = f"NR-{current_year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.public_id} - {self.name}"
    
# -------------------------------
# Record Access Control
# -------------------------------
class RecordAccess(models.Model):
    """
    Defines which user has access to which record.
    Controlled by admin.
    """

    class AccessType(models.TextChoices):
        VIEW = 'VIEW', 'View Only'
        EDIT = 'EDIT', 'Edit Access'

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='record_access'
    )

    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='user_access'
    )

    access_type = models.CharField(
        max_length=10,
        choices=AccessType.choices,
        default=AccessType.VIEW
    )

    # Audit info (important later)
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='access_assigned'
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'record')  # prevent duplicates

    def __str__(self):
        return f"{self.user.public_id} → {self.record.public_id} ({self.access_type})"