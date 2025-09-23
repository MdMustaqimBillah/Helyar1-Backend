from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id"]
        
        
class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = SubCategory
        fields = ["id", "category", "name", "slug", "description",]
        read_only_fields = ["id"]
        
class ProductSerializer(serializers.ModelSerializer):
    subcategory = SubCategorySerializer(read_only=True)


    class Meta:
        model = Product
        fields = [
            "id",
            "subcategory",
            "name",
            "slug",
            "description",
            "image",
            "price",
            "available",
            "retailer_url",
        ]
        read_only_fields = ["id"]
        
        
class CouponSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "product",
            "code",
            "description",
            "discount_percent",
            "discount_amount",
            "usage_type",
            "valid_from",
            "valid_to",
            "active",
        ]
        read_only_fields = ["id"]