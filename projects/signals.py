# projects/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure every User has a linked UserProfile.
    - On creation: make a new UserProfile.
    - On update: ensure it exists and save it.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        profile.save()
