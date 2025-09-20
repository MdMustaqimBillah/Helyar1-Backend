from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from accounts.models import User, EmailVerification
from datetime import timedelta
import secrets


@receiver(post_save, sender=User)
def create_mail_verification_signal(sender, instance, created, **kwargs):
    if created:
        token = secrets.token_hex(32)
        EmailVerification.objects.create(
            user=instance,
            token=token,
            expires_at= timezone.now()+timedelta(hours=1)
        )