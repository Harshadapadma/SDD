"""
Security Event Logger for Negen SDD.
Logs security-relevant events to both the AuditLog database table
and a dedicated security.log file via Python's logging module.
"""

import logging
from django.utils import timezone

security_logger = logging.getLogger('security')


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxied connections."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def log_security_event(event_type: str, request=None, user=None, details: str = '', level: str = 'INFO'):
    """
    Log a security event to both:
    1. Python security logger (writes to security.log file)
    2. AuditLog database table (if user is provided)

    Event types:
    - LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT
    - MFA_SENT, MFA_SUCCESS, MFA_FAILED, MFA_EXPIRED, MFA_LOCKED
    - PASSWORD_RESET_REQUEST, PASSWORD_CHANGE
    - ACCOUNT_LOCKOUT
    - ROLE_CHANGE
    - PERMISSION_DENIED
    - RATE_LIMIT_HIT
    - TOKEN_REFRESH, TOKEN_REFRESH_FAILED
    """
    ip = get_client_ip(request) if request else 'N/A'
    user_id = ''
    user_email = ''

    if user:
        user_id = getattr(user, 'public_id', str(getattr(user, 'id', '')))
        user_email = getattr(user, 'email', '')

    # Log to security.log file
    log_msg = f"[{event_type}] user={user_email} id={user_id} ip={ip} | {details}"
    log_fn = getattr(security_logger, level.lower(), security_logger.info)
    log_fn(log_msg)
