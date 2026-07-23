"""
Security models for Negen SDD.
- MFAChallenge: Stores Email OTP challenges for ADMIN/COMPLIANCE_OFFICER MFA.
- FailedLoginAttempt: Tracks failed login attempts for account lockout.
"""

import uuid
import hashlib
import secrets
from django.db import models
from django.utils import timezone
from datetime import timedelta


class MFAChallenge(models.Model):
    """
    Stores a pending Email OTP challenge.
    OTP code is hashed (SHA-256) before storage — never stored in plaintext.
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='mfa_challenges')
    otp_hash = models.CharField(max_length=64)  # SHA-256 hex digest
    session_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    OTP_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 5

    @staticmethod
    def hash_otp(otp_code: str) -> str:
        return hashlib.sha256(otp_code.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        """Generate a cryptographically secure 6-digit OTP."""
        return f"{secrets.randbelow(1000000):06d}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.created_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

    @property
    def is_locked(self) -> bool:
        return self.attempts >= self.MAX_ATTEMPTS

    def verify(self, otp_code: str) -> bool:
        """
        Verify the OTP. Returns True on success, False on failure.
        Increments attempt count on failure. Marks as used on success.
        """
        if self.is_used or self.is_expired or self.is_locked:
            return False

        if self.hash_otp(otp_code) == self.otp_hash:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
        else:
            self.attempts += 1
            self.save(update_fields=['attempts'])
            return False

    def __str__(self):
        return f"MFA Challenge for {self.user.email} ({self.session_token})"

    class Meta:
        ordering = ['-created_at']


class FailedLoginAttempt(models.Model):
    """
    Tracks failed login attempts per email for account lockout enforcement.
    """
    email = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    LOCKOUT_THRESHOLD = 10  # Max failed attempts before lockout
    LOCKOUT_WINDOW_MINUTES = 15  # Window to count failures

    @classmethod
    def is_locked_out(cls, email: str) -> bool:
        """Check if the email is currently locked out."""
        window_start = timezone.now() - timedelta(minutes=cls.LOCKOUT_WINDOW_MINUTES)
        count = cls.objects.filter(email__iexact=email, timestamp__gte=window_start).count()
        return count >= cls.LOCKOUT_THRESHOLD

    @classmethod
    def record_failure(cls, email: str, ip_address: str = None):
        """Record a failed login attempt."""
        cls.objects.create(email=email.lower(), ip_address=ip_address)

    @classmethod
    def clear_failures(cls, email: str):
        """Clear all failure records for an email (called on successful login)."""
        cls.objects.filter(email__iexact=email).delete()

    def __str__(self):
        return f"Failed login: {self.email} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
