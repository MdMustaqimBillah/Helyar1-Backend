from django.db import models
from accounts.models import User

# Create your models here.


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_id = models.CharField(max_length=100,blank=True,null=True)    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    