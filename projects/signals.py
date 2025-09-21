from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User  # or get_user_model if you switched to custom
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Prevent duplicate profiles — create only if none exists
        UserProfile.objects.get_or_create(user=instance)
