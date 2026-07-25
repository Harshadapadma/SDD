from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'

    def ready(self):
        """
        Runs whenever the application starts (Gunicorn WSGI or runserver).
        Automatically checks and creates/updates default admin & compliance officer.
        """
        import sys
        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'test', 'check'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        from django.core.management import call_command
        try:
            call_command('setup_admin')
        except Exception:
            pass
