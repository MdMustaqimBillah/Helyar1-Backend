from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings


from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse


from .models import *
from .serializers import *


import logging
logger = logging.getLogger(__name__)
# Create your views here.


class UserRegistrationView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [ AllowAny ]
    
    @extend_schema(
        tags=['accounts'],
        request=UserSerializer,
        responses={
            200: OpenApiResponse(description="Verification mail has been sent"),
            400: OpenApiResponse(description="Bad request (e.g., email sending failed)"),
        },
        description="Register a new user and send a verification email with token.",
        summary="User Registration",
    )
    
    def create(self, request, *args, **kwargs ):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        
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
    
    @extend_schema(
        tags=['accounts'],
        request=UserSerializer,
        responses={
            200: OpenApiResponse(description="Mail has been verified successfully"),
            404: OpenApiResponse(description="Invalid token passed"),
            408: OpenApiResponse(description="Token expired, please register again"),
        },
        description="Verification of email with token.",
        summary="Email Verification",
    )
    
    def get(self, request, token):
        
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
                        status=status.HTTP_200_OK
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
    
    
    @extend_schema(
        tags=["accounts"],
        request=LoginSerializer,
        responses={
            202: LoginResponseSerializer,
            400: OpenApiResponse(description="Error: Bad Request"),
            500: OpenApiResponse(description="Error: Internal Server Error"),
        },
        description="Login a user and return JWT tokens.",
        summary="User Login",
    )
    
    def post(self, request):
        try:
            serializer=LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data["user"]
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
            
        except serializer.ValidationError as e:
            logger.error("Validation error during login", exc_info=True)
            return Response (
                {"detail": str(e)},
                status = status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error("Error during login", exc_info=True)
            return Response (
                {"detail": str(e)},
                status = status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            



class ResendMailVerificationView(APIView):
    permission_classes=[AllowAny]
    
    @extend_schema(
        tags=['accounts'],
        request=ResendVerificationRequestSerializer,
        responses={
            200: OpenApiResponse(description="Verification mail has been sent"),
            400: OpenApiResponse(description="Error: Bad Request, mail already verified"),
            404: OpenApiResponse(description="Error: User not found"),
        },
        description="Resend verification email with token.",
        summary="Resend Verification Email",
    )
    
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        try:
            user = User.objects.get(email=email, password=password)
                
            if user.mail_verified:
                return Response(
                    {"detail":"Mail is already verified. Please login."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            else:
                mail_obj = EmailVerification.objects.get(user=user)
                logger.debug(f"Checking for mail object: {mail_obj}")
                
                token = mail_obj.token
                mail_obj.expires_at = timezone.now() + timezone.timedelta(hours=1)
                mail_obj.save()
                
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
        except User.DoesNotExist:
            return Response(
                {"detail":"Invalid email or password."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        