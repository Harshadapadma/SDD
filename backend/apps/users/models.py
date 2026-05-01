from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# -------------------------------
# Role Choices
# -------------------------------
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    COLLABORATOR = 'COLLABORATOR', 'Collaborator'
    VIEWER = 'VIEWER', 'Viewer'


# -------------------------------
# Custom User Manager
# -------------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role=UserRole.VIEWER, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            name=name,
            role=role,
            **extra_fields
        )

        # If password not provided → unusable (for email activation flow)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        return self.create_user(email, name, password, **extra_fields)


# -------------------------------
# User Model
# -------------------------------
class User(AbstractBaseUser, PermissionsMixin):
    # Public ID like: NEGSDD0001
    public_id = models.CharField(max_length=20, unique=True, editable=False)

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    employee_code = models.CharField(max_length=50, blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VIEWER
    )

    # Status flags
    is_active = models.BooleanField(default=False)  # user activates via email
    is_staff = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

    # Profile details
    designation = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)

    # Security / onboarding
    must_change_password = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)

    @property
    def is_profile_complete(self):
        return bool(self.designation and self.company_name and self.mobile_number)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def save(self, *args, **kwargs):
        """
        Auto-generate public_id like NEGSDD0001
        Runs only when creating a new user (no public_id yet)
        """
        if not self.public_id:
            last_user = User.objects.order_by('-id').first()

            if last_user and last_user.public_id:
                # Extract number from last ID
                last_number = int(last_user.public_id.replace('NEGSDD', ''))
                new_number = last_number + 1
            else:
                new_number = 1

            # Format with leading zeros → 0001
            self.public_id = f"NEGSDD{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.public_id} - {self.email}"