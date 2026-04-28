from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            quantics=0,
            first_name=instance.first_name,
            last_name=instance.last_name,
            age=18,  # Укажите значение по умолчанию
            kvantum='IT'  # Укажите значение по умолчанию
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()