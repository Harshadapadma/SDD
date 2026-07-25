"""
Security Headers Middleware for Negen SDD.
Injects Content-Security-Policy, Referrer-Policy, Permissions-Policy,
and X-Content-Type-Options on every HTTP response.
"""

from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to all responses.
    Placed after SecurityMiddleware in the MIDDLEWARE list.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Build CSP directives based on environment
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        cors_allowed = " ".join(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))

        if not settings.DEBUG:
            api_origins = f"'self' https: {frontend_url} {cors_allowed}".strip()
        else:
            api_origins = f"'self' http://127.0.0.1:8000 http://localhost:8000 http://localhost:5173 http://127.0.0.1:5173 {frontend_url} {cors_allowed}".strip()

        self.csp = "; ".join([
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
            "img-src 'self' data: blob:",
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com",
            f"connect-src {api_origins}",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ])

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy
        response['Content-Security-Policy'] = self.csp

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy (disable unused browser APIs)
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        return response
