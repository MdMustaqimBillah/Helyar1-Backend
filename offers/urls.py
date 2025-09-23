from django.urls import path
from .views import *


urlpatterns = [
    path('subcategories/<slug:slug>/', CategoryListView.as_view()),
    path('product/<slug:slug>/', ProductDetailView.as_view()),
    path('coupon/<slug:slug>/', CouponDetailView.as_view()),
]