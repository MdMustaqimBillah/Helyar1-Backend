from rest_framework import serializers
from rest_framework.validators import ValidationError
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'price', 'payment_id', 
            'subscription_id', 'status', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'price']  # price auto-set in model

class CreateCheckoutSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=['basic', 'premium'])