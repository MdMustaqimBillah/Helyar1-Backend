from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Subscription
from .serializers import SubscriptionSerializer
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
import stripe
import logging
import decimal


logger = logging.getLogger(__name__)


# Create your views here.

stripe.api_key = settings.STRIPE_API_KEY

class CheckOutView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
    
        try:
            # Create Stripe Checkout Session (test mode)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',  # Test with USD
                            'product_data': {
                                'name': 'Lifetime Access',
                            },
                            'unit_amount': int(serializer.validated_data['price'] * 100),  # Convert to cents
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',  # One-time payment
                success_url=f"{settings.DOMAIN}/subscriptions/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.DOMAIN}/subscriptions/cancel/",
                metadata={
                    'user_id': str(request.user.id),
                    'plan': serializer.validated_data['plan'],
                    'price': str(serializer.validated_data['price']),
                }
            )
            logger.info(f"Created Stripe Checkout Session: {checkout_session.id} for user {request.user.id}")
            return Response({
                'session_url': checkout_session.url,
                'message': 'Redirecting to Stripe Checkout...'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating Stripe session: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        try:
            user_id = session['metadata']['user_id']
            plan = session['metadata']['plan']
            price = decimal.Decimal(session['metadata']['price'])
            
            # Create or update subscription
            subscription, created = Subscription.objects.get_or_create(
                user_id=user_id,
                plan=plan,
                defaults={
                    'price': price,
                    'is_active': True,
                    'payment_id': session['payment_intent'],
                    'subscription_id': session['id']
                }
            )
            if not created:
                subscription.is_active = True
                subscription.payment_id = session['payment_intent']
                subscription.subscription_id = session['id']
                subscription.save()
            
            logger.info(f"Subscription {'created' if created else 'updated'} for user {user_id}")
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': 'Webhook processing failed'}, status=400)

    return JsonResponse({'status': 'success'}, status=200)

def success_view(request):
    session_id = request.GET.get('session_id', 'N/A')
    return render(request, 'subscriptions/success.html', {'session_id': session_id})

def cancel_view(request):
    return render(request, 'subscriptions/cancel.html')