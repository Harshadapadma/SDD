import os
import sys

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

# Initialize Django WSGI Application
application = get_wsgi_application()

try:
    from firebase_functions import https_fn

    @https_fn.on_request(
        max_instances=10,
        cors=https_fn.CorsOptions(
            cors_origins="*",
            cors_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        )
    )
    def api(req: https_fn.Request) -> https_fn.Response:
        """
        Firebase Cloud Function HTTP Entrypoint forwarding requests to Django WSGI handler.
        """
        return https_fn.Response.from_app(application, req.environ)
except ImportError:
    # Graceful fallback when firebase-functions is not installed locally
    pass
