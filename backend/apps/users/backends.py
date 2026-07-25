from django.contrib.auth.backends import BaseBackend
from .models import User


class EmailBackend(BaseBackend):
    """
    Custom authentication backend using email instead of username
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        clean_email = str(email).strip().lower()
        try:
            user = User.objects.get(email__iexact=clean_email)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None