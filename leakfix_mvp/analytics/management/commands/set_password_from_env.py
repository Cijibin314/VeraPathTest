import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    """
    Sets the password for a user specified by an environment variable.
    This is useful for resetting an admin password in a non-interactive way.
    """
    help = "Sets a user's password from DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.ERROR('Missing required environment variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD'))
            return

        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist.'))
            return

        self.stdout.write(f'Setting password for user "{username}"...')
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Password for user "{username}" set successfully.'))