from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import serializers


from .models import *

import requests
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

        phone_number=data["phone_no"]
        
        api_key = settings.PHONE_NUMBER_VALIDATION_API_KEY
        
        url =f"https://phonevalidation.abstractapi.com/v1/?api_key={api_key}&phone={phone_number}&country_code=GB"
        try:
            
            response = requests.get(url)
            result = response.json()
        except Exception as e:
            logger.error(f"Error during phone number validation: {e}", exc_info=True)
            raise serializers.ValidationError("Error validating phone number. Please try again later.")
        
        logger.debug(f"Phone validation response: {result}")
        
        if not result['valid']:
            raise serializers.ValidationError("Invalid phone number")
        data["phone_no"]=result['format']["international"]
        
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
        

class EmailVerificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    class Meta:
        model = EmailVerification
        read_only_fields = [
            'id','token','expires_at'
        ]
        
        
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
            user = authenticate(email=email, password=password)        
            
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
    password = serializers.CharField()



class ForgetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_mail(self):
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return self.email

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password2 = serializers.CharField()
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Password doesn't match")
        
        if len(data['password']) <8:
            raise serializers.ValidationError("Password is too small. At least 8 characters. ")
        
        return data
    


class ResetCodeSerializer(serializers.Serializer):
    user = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = ResetCode
        fields = ['id','code','created_at']