from django.db import models
from accounts.models import User

# Create your models here.


class UserProfile(models.Model):
    STATUS = [
        ('employed', 'Employed'),
        ('retired', 'Retired'),
        ('volunteer', 'Volunteer')
    ]
    
    
    JOB = [
        ('ambulance_service','Ambulance Service'),
        ('apha','APHA'),
        ('blood_bike','Blood Bike'),
        ('dental_practice','Dental Practice')
    ]
    
    
    EMPLOYER = [
        ('ambulance_service','Ambulance Service'),
        ('fire_service','Fire Service'),
        ('hm_coustguard','HM Coastguard'),
        ('independent_lifeboat','Independent Lifeboat'),
        ('nhs','NHS'),
        ('police','Police'),
        ('red_cross','Red Cross'),
        ('rnli','RNLI'),
        ('search_and_rescue','Search and Rescue')
    ]
    
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employment_status = models.CharField(max_length=100, choices=STATUS, default='employed')
    job_details = models.TextField(max_length=100, choices=JOB, default='ambulance')
    employer = models.CharField(max_length=100, choices=EMPLOYER, default='ambulance')
    id_card_front = models.FileField(upload_to='id_cards/', null=True, blank=True)
    id_card_back = models.FileField(upload_to='id_cards/', null=True, blank=True)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    subscription_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"