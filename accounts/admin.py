from django.contrib import admin
from .models import User,EmailVerification

# Register your models here.

class EmailVerificationInline(admin.StackedInline):
    model = EmailVerification
    can_delete = True
    verbose_name_plural = 'Email Verification'

class UserAdmin(admin.ModelAdmin):
    list_display =['email','first_name','last_name','role','is_staff','is_active','mail_verified','phone_no', 'joins']
    
    search_fields = [
        'email','first_name','last_name','role','phone_no','is_active', 'mail_verified'
    ]
    
    list_filter = [
        'email','is_active','role','phone_no', 'notification_type', 'joins', 'mail_verified'
    ]
    
    inlines=[EmailVerificationInline]
    
    
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display=[
        'get_user_email','token','expires_at' # used get_user_email to get the user mail to show in dashboard. cz it often doesn't support user__email ( __ lookups)
    ]
    
    def get_user_email(self,obj):
        return obj.user.email
    
    get_user_email.short_description = 'User Email' # By short description we set field name
    
    search_fields=[
        'user__email','token'
    ]
    
admin.site.register(User,UserAdmin)
admin.site.register(EmailVerification,EmailVerificationAdmin)