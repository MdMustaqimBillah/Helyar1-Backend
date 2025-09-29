from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import User, EmailVerification, PasswordResetCode, RetailerAccountRequest


# ------------------------
# Inline for Email Verification
# ------------------------
class EmailVerificationInline(admin.StackedInline):
    model = EmailVerification
    can_delete = True
    verbose_name_plural = 'Email Verification'


# ------------------------
# User Admin
# ------------------------
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'first_name', 'last_name', 'role',
        'is_staff', 'is_active', 'mail_verified',
        'phone_no', 'joins'
    ]

    search_fields = [
        'email', 'first_name', 'last_name',
        'role', 'phone_no', 'is_active', 'mail_verified'
    ]

    list_filter = [
        'email', 'is_active', 'role',
        'phone_no', 'notification_type',
        'joins', 'mail_verified'
    ]

    inlines = [EmailVerificationInline]

    # ✅ Admins can see everything, Retailers cannot see this app
    def save_model(self, request, obj, form, change):
        # If this is a new user or password changed
        raw_password = form.cleaned_data.get("password")
        if raw_password:
            obj.set_password(raw_password)  # ✅ Hash the password

        # Force retailer users to be staff + active
        if obj.role == "retailer":
            obj.is_staff = True
            obj.is_active = True

        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_module_permission(request)


# ------------------------
# Email Verification Admin
# ------------------------
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['get_user_email', 'token', 'expires_at']

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'

    search_fields = ['user__email', 'token']

    def has_module_permission(self, request):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_view_permission(request, obj)


# ------------------------
# Password Reset Admin
# ------------------------
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ['get_user_email', 'code', 'created_at', 'used', 'expires_at']

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'

    search_fields = ['user__email', 'code']
    list_filter = ['used', 'created_at', 'expires_at']

    def has_module_permission(self, request):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_view_permission(request, obj)


# ------------------------
# Retailer Account Request Admin
# ------------------------
class RetailerAccountRequestAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner_name", "contact_email", "account_created", "submitted_at")

    def has_module_permission(self, request):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Retailer").exists():
            return False
        return super().has_view_permission(request, obj)


# ------------------------
# Register models
# ------------------------
admin.site.register(User, UserAdmin)
admin.site.register(EmailVerification, EmailVerificationAdmin)
admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)
admin.site.register(RetailerAccountRequest, RetailerAccountRequestAdmin)
