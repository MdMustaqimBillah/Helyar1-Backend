from django.shortcuts import render


from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status


from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import *
from accounts.models import User
from .serializers import *
from custom_permissions.retailer_permission import IsOwner


# Create your views here.

class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=["Offers"],
        request=CategorySerializer,
        responses={200: OpenApiResponse(description="Categories fetched successfully")},
        summary="Fetch all categories with their subcategories and products",
        description="Retrieve a list of all categories, each with their associated subcategories and products.",
    )

    def get(self, request,slug):
        categories = Category.objects.prefetch_related("subcategories__products").get(slug=slug)
        if not categories:
            return Response(
                {"detail":"Category not found"},
                status = status.HTTP_404_NOT_FOUND
            )
            
        serializer = CategorySerializer(categories, many=True)
        return Response(
            {   
                "detail":"Categories fetched successfully",
                "data":serializer.data
                },
                status = status.HTTP_200_OK
            )

        

class ProductDetailView(RetrieveAPIView):
    
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    @extend_schema(
    tags=["Offers"],
    request=ProductSerializer,
    responses={200: OpenApiResponse(description="Categories fetched successfully")},
    summary="Fetch all categories with their subcategories and products",
    description="Retrieve a list of all categories, each with their associated subcategories and products.",
    )
    
    def get (self, request,slug):
        products = Product.objects.get(slug=slug)
        serializer = ProductSerializer(products)
        return Response(serializer.data)
    
    

class CouponDetailView(RetrieveAPIView):
    
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    @extend_schema(
    tags=["Offers"],
    request=CouponSerializer,
    responses={200: OpenApiResponse(description="Categories fetched successfully")},
    summary="Fetch all categories with their subcategories and products",
    description="Retrieve a list of all categories, each with their associated subcategories and products.",
    )
    
    def get (self, request,slug):
        try:
            product = Product.objects.prefetch_related("coupons").get(slug=slug)
        except Product.DoesNotExist:
            return Response(
                {"detail":"Coupon not found"},
                status = status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductSerializer(product)
        return Response({
            'details':'You have got a coupon.',
            'data':serializer.data},
             status = status.HTTP_200_OK)