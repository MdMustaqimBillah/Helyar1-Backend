import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.models import User
from .models import Subscription
from .serializers import SubscriptionSerializer, CreateCheckoutSerializer

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_API_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateCheckoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"details": "Serializer is not valid", "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan = serializer.validated_data['plan']
        user = request.user
        
        # Check if user already has active subscription
        if Subscription.objects.filter(user=user, is_active=True).exists():
            return Response(
                {"details": "You have already subscribed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get price from settings
        price_cents = settings.STRIPE_PRICES.get(plan)
        if not price_cents:
            return Response(
                {"details": "Invalid plan"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': price_cents,  # Already in cents from settings
                        'product_data': {
                            'name': f'{plan.capitalize()} Subscription',
                            'description': f'One-time payment for {plan} plan',
                        },
                    },
                    'quantity': 1
                }],
                mode='payment',
                billing_address_collection='required',
                success_url=settings.DOMAIN + '/subscription/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.DOMAIN + '/subscription/cancel',
                customer_email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'plan': plan,
                }
            )
            
            # Create subscription record
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'subscription_id': checkout_session.id,
                    'status': 'inactive',
                    'is_active': False
                }
            )
            
            if not created:
                subscription.plan = plan
                subscription.subscription_id = checkout_session.id
                subscription.status = 'inactive'
                subscription.is_active = False
                subscription.save()
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            }, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckoutSuccessView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Session ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            try:
                user = request.user
                user.subscribed=True
            except User.DoesNotExist:
                return Response(
                    {"details":"User not found."},
                    status = status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'message': 'Payment successful! Your subscription will be activated shortly.',
                'payment_status': session.payment_status,
                'session_id': session_id
            }, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error("Invalid Payload")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Signature")
            return HttpResponse(status=400)
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            logger.info(f"✓ Checkout session completed: {session['id']}")
            
            user_id = session['metadata'].get('user_id')
            plan = session['metadata'].get('plan')
            
            if user_id and session['payment_status'] == 'paid':
                try:
                    user = User.objects.get(id=user_id)
                    
                    subscription, created = Subscription.objects.get_or_create(
                        user=user,
                        defaults={
                            'plan': plan,
                            'payment_id': session.get('payment_intent'),
                            'subscription_id': session['id'],
                            'status': 'active',
                            'is_active': True
                        }
                    )
                    
                    if not created:
                        subscription.plan = plan
                        subscription.payment_id = session.get('payment_intent')
                        subscription.subscription_id = session['id']
                        subscription.status = 'active'
                        subscription.is_active = True
                        subscription.save()
                    
                    logger.info(f"✓ Subscription activated for {user.email}")
                    logger.info(f"  Plan: {plan}")
                    logger.info(f"  Payment ID: {session.get('payment_intent')}")
                    
                except User.DoesNotExist:
                    logger.error(f"✗ User {user_id} not found")
                except Exception as e:
                    logger.error(f"✗ Error activating subscription: {str(e)}")
            else:
                logger.warning(f"⚠ Payment not completed or missing user_id")
        
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            logger.info(f"⚠ Checkout session expired: {session['id']}")
        
        return HttpResponse(status=200)


class SubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response(
                {'message': 'No subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            
            if not subscription.is_active:
                return Response(
                    {'error': 'Subscription is not active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription.status = 'cancelled'
            subscription.is_active = False
            subscription.save()
            
            return Response({
                'message': 'Subscription cancelled successfully',
                'subscription': SubscriptionSerializer(subscription).data
            }, status=status.HTTP_200_OK)
            
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )