import os
from django.core.management.base import BaseCommand
from apps.users.models import User, UserRole
from django.conf import settings

class Command(BaseCommand):
    help = 'Create a superuser from environment variables if it does not exist'

    def handle(self, *args, **options):
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@negensdd.com')
        admin_password = os.getenv('ADMIN_PASSWORD', '37mG%abJzYrB!WA4')
        admin_name = os.getenv('ADMIN_NAME', 'Administrator')

        user = User.objects.filter(email=admin_email).first()
        if not user:
            self.stdout.write(f'Creating superuser: {admin_email}...')
            User.objects.create_superuser(
                email=admin_email,
                name=admin_name,
                password=admin_password
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin account: {admin_email}'))
        else:
            self.stdout.write(f'Updating superuser: {admin_email}...')
            user.name = admin_name
            user.set_password(admin_password)
            user.role = UserRole.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated admin account: {admin_email}'))

        # Seed Compliance Officer
        comp_email = os.getenv('COMPLIANCE_EMAIL', 'compliance@negensdd.com')
        comp_password = os.getenv('COMPLIANCE_PASSWORD', '&u1krM3VSrhm^O*M')
        comp_name = os.getenv('COMPLIANCE_NAME', 'Compliance Manager')

        if comp_email and comp_password:
            comp_user = User.objects.filter(email=comp_email).first()
            if not comp_user:
                self.stdout.write(f'Creating compliance officer: {comp_email}...')
                User.objects.create_user(
                    email=comp_email,
                    name=comp_name,
                    password=comp_password,
                    role=UserRole.COMPLIANCE_OFFICER,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created compliance officer account: {comp_email}'))
            else:
                self.stdout.write(f'Updating compliance officer: {comp_email}...')
                comp_user.name = comp_name
                comp_user.set_password(comp_password)
                comp_user.role = UserRole.COMPLIANCE_OFFICER
                comp_user.is_active = True
                comp_user.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated compliance officer account: {comp_email}'))

