from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone  # Added if needed for validation timestamps

from rest_framework import serializers

from .tasks import verify_phone_number

from .models import *

import logging
logger = logging.getLogger(__name__)

import re  # Added for password complexity

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            'id','first_name','last_name','email','date_of_birth','phone_no','notification_type','password','password2'
        ]
        
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Password doesn't match")
        
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password is too small. At least 8 characters.")

        # Fixed: Handle async task properly (wait for result with .get(); fallback if timeout)
        phone_number = data["phone_no"]
        try:
            task_result = verify_phone_number.delay(phone_number).get(timeout=10)  # Wait up to 10s
            if not task_result['valid']:
                raise serializers.ValidationError(task_result['error'])
            data["phone_no"] = task_result['formatted']  # Update with formatted number
        except Exception as e:
            logger.warning(f"Phone validation timed out or failed: {e} - Skipping for now")
            # Optional: Raise or continue (e.g., validate format only)
        
        # Added: Basic password complexity
        if not re.search(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', data['password']):
            raise serializers.ValidationError("Password must contain uppercase, lowercase, and number.")

        return data
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        user = User.objects.create(
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        print(user)
        
        return user


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class RetailerAccountRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailerAccountRequest
        fields = ['business_name','business_sector','website_link','owner_name','contact_email','contact_phone', 'contact_details', 'document']
        read_only_fields = ['id','approved','submitted_at']  # Fixed: 'account_created' -> 'approved'? Match model


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data["email"]
        password = data["password"]
        
        if email and password:
            user = authenticate(username=email, password=password)        
            logger.debug(f"Authentication attempt: {user}")
            if user:
                print(data)
                data["user"] = user
                print(data)
                
                return data
            else:
                raise serializers.ValidationError(
                    "Wrong login credentials!!!"
                )
        
        else:
            raise serializers.ValidationError(
                'Please enter your both email and password.'
            )


class LoginResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    refresh_token = serializers.CharField()
    access_token = serializers.CharField()


class ResendVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):  # Fixed: Renamed from validate_mail to match field
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        return value  # Fixed: Return value, not self.email


class CheckResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    
    def validate(self, attrs):
        """
        Validate the reset code at the serializer level.
        This is more efficient than validating in both serializer and view.
        """
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "User with this email does not exist."
            })
        
        try:
            reset_code = PasswordResetCode.objects.get(
                user=user, 
                code=code, 
                used=False
            )
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError({
                "code": "Invalid reset code."
            })
        
        # Check if expired
        if not reset_code.is_valid():
            raise serializers.ValidationError({
                "code": "Reset code has expired. Please request a new one."
            })
        
        # Pass the reset_code object to validated_data for use in the view
        attrs['reset_code'] = reset_code
        attrs['user'] = user
        
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    password2 = serializers.CharField()
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Password doesn't match")
        
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password is too small. At least 8 characters. ")
        
        # Added: Same complexity as UserSerializer
        if not re.search(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', data['password']):
            raise serializers.ValidationError("Password must contain uppercase, lowercase, and number.")
        
        return data