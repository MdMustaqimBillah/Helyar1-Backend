from django.db import models
from accounts.models import User

class Subscription(models.Model):
    STATUS = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("inactive", "Inactive")
    ]
    
    SUBSCRIPTION_TYPE = [
        ("basic", "Basic"),
        ("premium", "Premium")
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=30, choices=SUBSCRIPTION_TYPE)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS, default="inactive")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan}"
    
    def save(self, *args, **kwargs):
        # Automatically set price based on plan
        if self.plan == 'basic':
            self.price = 5.99
        elif self.plan == 'premium':
            self.price = 9.99
            
        super().save(*args, **kwargs)  # Fixed: removed self