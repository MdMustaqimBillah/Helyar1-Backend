from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import serializers

from .tasks import verify_phone_number

from .models import *

import logging
logger = logging.getLogger(__name__)

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
        
        if len(data['password']) <8:
            raise serializers.ValidationError("Password is too small. At least 8 characters. ")

        # phone_number=data["phone_no"]
        
        # result=verify_phone_number(phone_number)
        
        # data["phone_no"]=result['format']["international"]
        
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
    
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data ):
        email = data["email"]
        password = data["password"]
        
        if email and password:
            user = authenticate(username=email, password=password)        
            logger.debug(f"Authentication attempt: {user}")
            if user:
                print(data)
                data["user"]=user
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

    def validate_mail(self,value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return self.email

class ResetPasswordSerializer(serializers.Serializer):
    code = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()
    password2 = serializers.CharField()
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Password doesn't match")
        
        if len(data['password']) <8:
            raise serializers.ValidationError("Password is too small. At least 8 characters. ")
        
        return data
    
    def validate_code(self,value):
        try:
            email = self.initial_data.get("email")
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this email does not exist.")
            
            token = PasswordResetCode.objects.get(user=user, code=value, used=False)
            
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid reset code.")
        
        if token.expires_at and token.expires_at < timezone.now():
            raise serializers.ValidationError("This reset code has expired.")
        
        return value
    
