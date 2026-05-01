import os
from django.core.management.base import BaseCommand
from apps.users.models import User, UserRole
from django.conf import settings

class Command(BaseCommand):
    help = 'Create a superuser from environment variables if it does not exist'

    def handle(self, *args, **options):
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_name = os.getenv('ADMIN_NAME', 'Admin')

        if not admin_email or not admin_password:
            self.stdout.write(self.style.WARNING('ADMIN_EMAIL or ADMIN_PASSWORD not set in .env. Skipping admin setup.'))
            return

        if not User.objects.filter(email=admin_email).exists():
            self.stdout.write(f'Creating superuser: {admin_email}...')
            User.objects.create_superuser(
                email=admin_email,
                name=admin_name,
                password=admin_password
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin account: {admin_email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin account {admin_email} already exists.'))
