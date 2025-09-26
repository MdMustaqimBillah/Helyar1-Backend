from django.contrib import admin

from .models import *

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'description', 'slug']
    search_fields = ['name', 'slug', 'description']
    list_filter = ['name', 'slug']
    
    
    def get_object(self,obj):
        return obj.name
    
    get_object.short_description = 'Category Name' # By short description we set field's table(column) name
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['slug'].help_text = "Leave blank to auto-generate from name"
        form.base_fields['slug'].required = False
        return form
    

class SubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}    
    list_display = ['name', 'category', 'description', 'slug']
    search_fields = ['category__name','name', 'slug', 'description']
    list_filter = ['category', 'name', 'slug']
    
    
    def get_object(self,obj):
        return obj.name
    
    
    get_object.short_description = 'SubCategory Name' # By short description we set field's table(column) name
    
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['slug'].help_text = "Leave blank to auto-generate from name"
        form.base_fields['slug'].required = False
        return form

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = [ 'subcategory__category__name', 'subcategory','name', 'price', 'available']
    search_fields = ['subcategory__name','name', 'slug', 'description', 'price', 'available' ]
    list_filter = ['subcategory', 'price', 'available']
    
    
    def get_object(self,obj):
        return obj.name
    
    
    get_object.short_description = 'Product Name' # By short description we set field's table(column) name
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['slug'].help_text = "Leave blank to auto-generate from name"
        form.base_fields['slug'].required = False
        return form
    
    
class CouponAdmin(admin.ModelAdmin):
    list_display = ['product__name', 'code','discount_percent','discount_amount', 'description', 'start_date', 'end_date', 'usage_type', 'is_active']
    search_fields = ['product__name', 'code', 'usage_type','discount_percentage','discount_amount','start_date', 'end_date' ]
    list_filter = ['usage_type', 'start_date', 'end_date', 'is_active']
    
    
    def get_object(self,obj):
        return obj.code
    
    
    get_object.short_description = 'Coupon Code' # By short description we set field's table(column) name
    
    
    
    
admin.site.register(Category,CategoryAdmin)
admin.site.register(SubCategory,SubCategoryAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(Coupon,CouponAdmin)