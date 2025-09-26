
from django.core.mail import send_mail
from django.conf import settings


from rest_framework import serializers


import logging
logger = logging.getLogger(__name__)

import requests



def verify_phone_number(phone_number):
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
    
    
def mail_send(user,subject: str, message: str, code=None):
    try:
        send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
        logger.info("Password reset code email sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Error sending password reset code email: {e}", exc_info=True)
        return False