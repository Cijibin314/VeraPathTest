from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analytics.models import Practice, UserProfile

class Command(BaseCommand):
    help = 'Sets up a profile for the first superuser found and links it to the default practice.'

    def handle(self, *args, **options):
        # Find the first superuser
        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser:
                self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return

        # Find the default practice
        try:
            default_practice = Practice.objects.get(athena_practice_id='195900')
        except Practice.DoesNotExist:
            self.stdout.write(self.style.ERROR('Default practice not found. Please run the `create_default_practice` migration.'))
            return

        # Create a user profile for the superuser
        profile, created = UserProfile.objects.get_or_create(
            user=superuser,
            defaults={'practice': default_practice}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created profile for superuser "{superuser.username}" and linked to "{default_practice.name}".'))
        else:
            profile.practice = default_practice
            profile.save()
            self.stdout.write(self.style.WARNING(f'Profile for superuser "{superuser.username}" already existed. Ensured it is linked to "{default_practice.name}".'))
