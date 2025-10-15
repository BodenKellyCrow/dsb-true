from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projects.models import UserProfile

class Command(BaseCommand):
    help = 'Create missing UserProfiles for all users'

    def handle(self, *args, **kwargs):
        users_fixed = 0
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                users_fixed += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created profile for {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Fixed {users_fixed} users'))