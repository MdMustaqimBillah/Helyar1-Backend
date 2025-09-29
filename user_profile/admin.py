from django.contrib import admin
from .models import UserProfile

# Register your models here.

class UserProfileAdmin(admin.ModelAdmin):
    list_display =['user','employment_status','job_details','employer','subscription_status','address_line1','city','country','postcode', 'created_at']
    search_fields =['user__email']
    list_filter =['employment_status','employer','subscription_status']
    ordering =['-created_at','user__email']
    
    
    
admin.site.register(UserProfile, UserProfileAdmin)