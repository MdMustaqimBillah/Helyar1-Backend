from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings


from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import *


import logging
logger = logging.getLogger(__name__)
# Create your views here.


class UserRegistrationView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [ AllowAny ]
    
    logger.info("Start executing registration view.")
    
    def create(self, request, *args, **kwargs ):
        
        logger.info("Executing perform_create method of user registration")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        
        logger.info("Executing User creation.")
        user = serializer.save()
            
        mail_obj = EmailVerification.objects.get(user=user)
        logger.debug(f"Checking for mail object: {mail_obj}")
        
        token = mail_obj.token
        
        url = f'http://127.0.0.1:8000/api/accounts/mail-verification/{token}'
        try:
        
            send_mail(
                'Verify your mail',
                f'''Click on the link or copy & paste the like on your browser to verify your mail.
                
                Url: {url}
                
                Do not share this link with others for security reasons. The link will be valid for 1 hour
                ''',
                
                settings.EMAIL_HOST_USER,
                
                [user.email],
                
                fail_silently = False            
                
            )
            logger.info("Mail sent successfully.")
            
            return Response(
                {'detail':"Verification mail has been sent. Check your mail box."},
                status = status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error("Couldn't send mail",exc_info=True)
            return Response(
                {"detail": str(e)},
                status = status.HTTP_400_BAD_REQUEST
            )
            
        
        
class EmailVerificationView(APIView):
    permission_classes=[AllowAny]
    
    def get(self, request, token):
        logger.info("Entered inside Email Verification View")
        
        try:
            logger.info("Executing Try method for mail verification")
            verification_token = EmailVerification.objects.get(token=token)
            logger.info(f"Verification Token: {verification_token.token}")
            if verification_token.is_valid():
                user = verification_token.user
                user.is_active = True
                user.mail_verified = True
                user.save()
                verification_token.delete()

                ref_token = RefreshToken.for_user(user)
                logger.debug(f"refresh token : {str(ref_token)}")
                response = {
                    "email": user.email,
                    "first_name":user.first_name,
                    "last_name":user.last_name,
                    "refresh_token":str(ref_token),
                    #"access_token":str(ref_token.access)
                }

                return Response(
                        {
                            "detail": "Mail has been verified successfully",
                            "user_data": UserRegistrationSerializer(response).data
                        },
                        status=status.HTTP_201_CREATED
                    )


            else:
                user = verification_token.user
                user.delete()
                return Response (
                    {"detail":"Verification Expired. Please create a new account"},
                    status = status.HTTP_408_REQUEST_TIMEOUT
                )

        except EmailVerification.DoesNotExist:
            
            return Response (
                {"detail": "Token Not found"},
                status = status.HTTP_404_NOT_FOUND
            )
            
            
            
class UserLoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, **validated_data):
        user = validated_data["user"]
        email = user.email
        first_name = user.first_name
        last_name = user.last_name
        
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        
        response = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "refresh_token": refresh_token,
            "access_token": access_token
        }
        
        login_response = LoginResponseSerializer(response)
        
        logger.info(f"LoginResponse: {login_response}")
        
        logger.info(f"LoginResponse.data: {login_response.data}")
        
        return Response (
            {"detail": login_response.data},
            status = status.HTTP_202_ACCEPTED
        )