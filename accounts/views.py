from django.contrib.auth.models import update_last_login
from django.utils import timezone  # Fixed: Full import for timedelta/now
from django.urls import reverse
from django.core.mail import send_mail
from django.shortcuts import render
from django.conf import settings

from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import *
from .serializers import *
from .tasks import mail_send
from .services.google_auth import GoogleAuthService

import random
import logging
logger = logging.getLogger(__name__)
# Create your views here.


class UserRegistrationView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
            
        mail_obj = EmailVerification.objects.get(user=user)
        logger.debug(f"Checking for mail object: {mail_obj}")
        
        token = mail_obj.token
        
        # Build URL dynamically using request
        verification_path = reverse('mail-verification', kwargs={'token': token})
        # Get the full URL with domain
        url = request.build_absolute_uri(verification_path)
        
        try:
            subject = "Verify your mail"
            message = f'''Click on the link or copy & paste the link on your browser to verify your mail.
                
                Url: {url}
                
                Do not share this link with others for security reasons. The link will be valid for 1 hour
                '''
        
            mail_send.delay(user.email, subject, message)
            
            logger.info("Mail sent successfully.")
            
            return Response(
                {'detail': "Verification mail has been sent. Check your mail box."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error("Couldn't send mail", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
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
            logger.info(f"Received Token: {token}")
            verification_token = EmailVerification.objects.get(token=token)
            logger.debug(f"Verification Token Retrieved: {verification_token}")  # Fixed: debug instead of error
            
            logger.info(f"Verification Token: {verification_token.token}")
            logger.info(f"Token Validity: {verification_token.is_valid()}")
            if verification_token.is_valid():
                user = verification_token.user
                user.is_active = True
                user.mail_verified = True
                user.role = "customer"
                user.save()

                ref_token = RefreshToken.for_user(user)
                logger.debug(f"refresh token: {str(ref_token)}")
                response = {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "refresh_token": str(ref_token),
                    "access_token": str(ref_token.access_token)
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
                return Response(
                    {"detail": "Verification Expired. Please create a new account"},
                    status=status.HTTP_408_REQUEST_TIMEOUT
                )

        except EmailVerification.DoesNotExist:
            return Response(
                {"detail": "Token Not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ResendMailVerificationView(APIView):
    permission_classes = [AllowAny]
    
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
        password = request.data.get("password")  # Unused—remove if not needed?
        
        try:
            logger.info(f"Resend verification request for email: {email}")
            user = User.objects.get(email=email)
            logger.debug(f"User found: {user}")
            if user.mail_verified:
                logger.info("Mail is already verified. Please login.")
                return Response(
                    {"detail": "Mail is already verified. Please login."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            else:
                mail_obj = EmailVerification.objects.get(user=user)
                logger.debug(f"Checking for mail object: {mail_obj}")
                
                token = mail_obj.token
                mail_obj.expires_at = timezone.now() + timezone.timedelta(hours=1)  # Fixed: Use timezone
                mail_obj.save()
                
                # Build URL dynamically using request
                verification_path = reverse('mail-verification', kwargs={'token': token})
                # Get the full URL with domain
                url = request.build_absolute_uri(verification_path)
                
                try:
                    subject = 'Verify your mail'
                    message = f'''Click on the link or copy & paste the link on your browser to verify your mail.
                        
                        Url: {url}
                        
                        Do not share this link with others for security reasons. The link will be valid for 1 hour
                        '''
                        
                    mail_send.delay(user.email, subject, message)
                    
                    logger.info("Mail sent successfully.")
                    return Response(
                        {'detail': "Verification mail has been sent. Check your mail box."},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    logger.error("Couldn't send mail", exc_info=True)
                    return Response(
                        {"detail": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_404_NOT_FOUND
            )


class RetailerAccountRequestView(CreateAPIView):
    serializer_class = RetailerAccountRequestSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['accounts'],
        request=RetailerAccountRequestSerializer,
        responses={
            201: OpenApiResponse(description="Retailer account request submitted successfully"),
            400: OpenApiResponse(description="Bad request"),
        },
        description="Submit a retailer account request.",
        summary="Retailer Account Request",
    )
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {'detail': "Retailer account request submitted successfully."},
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            logger.error("Error submitting retailer account request", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            




class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['accounts'],
        description="Get Google OAuth URL for login (existing users only).",
        summary="Google Login Start",
    )
    def get(self, request):
        service = GoogleAuthService()
        auth_url, state = service.get_auth_url()
        # Store state in session for callback verification
        request.session['google_oauth_state'] = state
        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['accounts'],
        description="Google OAuth callback: Verify existing user and issue JWT.",
        summary="Google Login Callback",
    )
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        if not code or not state:
            return Response({'error': 'Missing code or state'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify state
        session_state = request.session.get('google_oauth_state')
        if state != session_state:
            return Response({'error': 'Invalid state'}, status=status.HTTP_400_BAD_REQUEST)
        del request.session['google_oauth_state']  # Clean up

        try:
            service = GoogleAuthService()
            google_user = service.get_user_from_code(code, state)

            if not google_user['verified']:
                return Response({'error': 'Email not verified by Google'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user exists (existing users only)
            try:
                user = User.objects.get(email=google_user['email'])
                if not user.is_active:
                    return Response({'error': 'Account inactive. Please verify email.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'No account found with this email. Please register first.'}, status=status.HTTP_404_NOT_FOUND)

            # Login: Generate JWT like UserLoginView
            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            refresh_token_str = str(refresh_token)

            response_data = {
                "email": user.email,
                "first_name": google_user.get('first_name', user.first_name),
                "last_name": google_user.get('last_name', user.last_name),
                "refresh_token": refresh_token_str,
                "access_token": access_token
            }

            return Response(
                {"detail": response_data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Google callback error: {e}", exc_info=True)
            return Response({'error': 'Authentication failed'}, status=status.HTTP_400_BAD_REQUEST)






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
            serializer = self.serializer_class(data=request.data)
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
            
            return Response(
                {"detail": login_response.data},
                status=status.HTTP_202_ACCEPTED
            )
            
        except serializers.ValidationError as e:
            logger.error("Validation error during login", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error("Error during login", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgetPasswordRequestView(APIView):
    permission_classes = [AllowAny]
    
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
            user = User.objects.get(email=email)
            
            token = PasswordResetCode.objects.create(user=user)
            token.code = f"{random.randint(243010, 999999)}"
            token.expires_at = timezone.now() + timezone.timedelta(minutes=10)
            token.save()             
            subject = "Password Reset Code"
        
            message = f'''Your password reset code is: {token.code}
                    
                    This code will expire in 10 minutes. Do not share this code with others for security reasons.
                    ''' 
            state = mail_send.delay(user.email, subject, message, code=token.code)
            
            if state:
                return Response(
                    {'detail': "Password reset code has been sent to your email."},
                    status=status.HTTP_200_OK
                ) 
                
                # Next part is handled by ResetPasswordView
            
        except User.DoesNotExist:
            return Response(
                {'detail': "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )


class CheckResetCodeView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['accounts'],
        request=CheckResetCodeSerializer,
        responses={
            200: OpenApiResponse(description="Reset code is valid"),
            400: OpenApiResponse(description="Error: Bad Request"),
        },
        description="Check if the reset code is valid.",
        summary="Check Reset Code",
    )
    def post(self, request):
        serializer = CheckResetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # All validation is done in serializer
        # Just mark the code as used and return success
        reset_code = serializer.validated_data['reset_code']
        reset_code.used = True
        reset_code.save()
        
        return Response(
            {'detail': "Reset code is valid."},
            status=status.HTTP_200_OK
        )

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
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
        password = serializer.validated_data.get("password")
        
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()   
            return Response(
                {'detail': "Password has been reset successfully."},
                status=status.HTTP_200_OK
            )              
        except User.DoesNotExist:
            return Response(
                {'detail': "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(  # Added: For docs
        tags=['accounts'],
        request=None,
        responses={
            200: OpenApiResponse(description="User logged out successfully"),
            400: OpenApiResponse(description="Invalid token"),
        },
        description="Logout user and blacklist token.",
        summary="User Logout",
    )
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")  # Get refresh token from request data
            
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Update user's last logout time
            user = request.user
            user.last_logout = timezone.now()  # Fixed: Use timezone.now()
            user.save(update_fields=["last_logout"])
            
            logger.info(f"User {user.id} logged out successfully")
            
            return Response(
                {"detail": "User logged out successfully."},
                status=status.HTTP_200_OK
            )
            
        except TokenError:
            logger.warning(f"Invalid refresh token provided for user {request.user.id}")
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error during logout for user {request.user.id}", exc_info=True)
            return Response(
                {"detail": "An error occurred during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )