from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'

    def ready(self):
        """
        Runs whenever the application starts.
        Automatically checks and creates the default admin from .env
        """
        import sys
        # Only attempt auto-setup when running the actual server
        if 'runserver' in sys.argv:
            from django.core.management import call_command
            try:
                # This ensures an admin exists without manual command entry
                call_command('setup_admin')
            except Exception:
                # If migrations haven't run yet, this will fail silently
                # preventing the server from crashing before it's ready.
                pass
