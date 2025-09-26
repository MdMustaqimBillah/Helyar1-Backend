from django.contrib.auth.models import update_last_login
from django.utils.timezone import now
from django.core.mail import send_mail
from django.shortcuts import render
from django.conf import settings


from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse


from .models import *
from .serializers import *
from .tasks import mail_send

import random
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
        
        url = f'http://127.0.0.1:8000/api/accounts/mail-verification/{token}/'
        try:
            subject = "Verify your mail"
            message =  f'''Click on the link or copy & paste the like on your browser to verify your mail.
                
                Url: {url}
                
                Do not share this link with others for security reasons. The link will be valid for 1 hour
                '''
        
            mail_send(subject,message,user)
            
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
        
        item = EmailVerification.objects.get(token=token)
        if item:
            logger.info(f"item object: {item}")
        
        try:
            logger.info("Executing Try method for mail verification")
            logger.info(f"Received Token: {token}")
            verification_token = EmailVerification.objects.get(token=token)
            logger.error(f"Verification Token Retrieved: {verification_token}")
            
            logger.info(f"Verification Token: {verification_token.token}")
            logger.info(f"Token Validty: {verification_token.is_valid()}")
            if verification_token.is_valid():
                user = verification_token.user
                user.is_active = True
                user.mail_verified = True
                user.role = "customer"
                user.save()

                ref_token = RefreshToken.for_user(user)
                logger.debug(f"refresh token : {str(ref_token)}")
                response = {
                    "email": user.email,
                    "first_name":user.first_name,
                    "last_name":user.last_name,
                    "refresh_token":str(ref_token),
                    "access_token":str(ref_token.access_token)
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
            logger.info(f"Resend verification request for email: {email}")
            user = User.objects.get(email=email)
            logger.debug(f"User found: {user}")
            if user.mail_verified:
                logger.info("Mail is already verified. Please login.")
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
                    subject = 'Verify your mail'
                    message = f'''Click on the link or copy & paste the like on your browser to verify your mail.
                        
                        Url: {url}
                        
                        Do not share this link with others for security reasons. The link will be valid for 1 hour
                        '''
                        
                    mail_send(subject,message,user)
                    
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
            serializer=self.serializer_class(data=request.data)
            logger.info(f"Login data received: {request.data}")
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data["user"]
            update_last_login(None, user)
            logger.info(f"Authenticated user: {user}")
            email = user.email
            first_name = user.first_name
            last_name = user.last_name
            
            refresh_token = RefreshToken.for_user(user)
            access_token = refresh_token.access_token
            
            response = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "refresh_token": str(refresh_token),
                "access_token": str(access_token)
            }
            
            login_response = LoginResponseSerializer(response)
            
            logger.info(f"LoginResponse: {login_response}")
            
            logger.info(f"LoginResponse.data: {login_response.data}")
            
            return Response (
                {"detail": login_response.data},
                status = status.HTTP_202_ACCEPTED
            )
            
        except serializers.ValidationError as e:
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
            







class ForgetPasswordRequestView(APIView):
    permission_classes=[AllowAny]
    
    @extend_schema(
        tags=['accounts'],
        request=ForgetPasswordRequestSerializer,
        responses={
            200: OpenApiResponse(description="Password has been reset successfully"),
            400: OpenApiResponse(description="Error: Bad Request"),
            404: OpenApiResponse(description="Error: User not found"),
        },
        description="Reset password for a user.",
        summary="Forget Password",
    )
    def post(self, request):
        serializer = ForgetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get("email")
        
        try:
            user=User.objects.get(email=email)
            
            token = PasswordResetCode.objects.create(user=user)
            token.code = f"{random.randint(243010,999999)}"
            token.expires_at = timezone.now() + timezone.timedelta(minutes=10)
            token.save()             
            subject = "Password Reset Code"
        
            message = f'''Your password reset code is: {token.code}
                    
                    This code will expire in 10 minutes. Do not share this code with others for security reasons.
                    ''' 
            state=mail_send(user,subject,message,code=token.code) # sending mail
            
            if state:
                return Response(
                    {'detail':"Password reset code has been sent to your email."},
                    status=status.HTTP_200_OK
                ) 
                
                # Next part is handled by ResetPasswordView
            
            
        except User.DoesNotExist:
            return Response(
                
                {'detail':"User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
            
            





    
    
class ResetPasswordView(APIView): # Actions very after ForgetPasswordRequestView
    permission_classes=[AllowAny]
    
    @extend_schema(
        tags=['accounts'],
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password has been reset successfully"),
            400: OpenApiResponse(description="Error: Bad Request"),
            404: OpenApiResponse(description="Error: User or Reset code not found"),
        },
        description="Reset password using reset code.",
        summary="Reset Password",
    )
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get("email")
        code = serializer.validated_data.get("code")
        password = serializer.validated_data.get("password")
        
        try:
            user = User.objects.get(email=email)
            
            try:
                reset_code = PasswordResetCode.objects.get(user=user, code=code, used=False)
                
                if reset_code.is_valid():
                    user.set_password(password)
                    user.save()
                    
                    reset_code.used = True
                    
                    return Response(
                        {'detail':"Password has been reset successfully."},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'detail':"Reset code has expired. Please request a new one."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except PasswordResetCode.DoesNotExist:
                return Response(
                    {'detail':"Invalid reset code."},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except User.DoesNotExist:
            return Response(
                {'detail':"User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
            
            
            
            
            

class UserLogoutView(APIView):
    permission_classes=[IsAuthenticated]    
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()
            user = request.user
            user.last_logout = now()
            user.save(update_fields=["last_logout"])
            
            return Response(
                {"detail":"User logged out successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error("Error during logout", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )