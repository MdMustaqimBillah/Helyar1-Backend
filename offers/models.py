from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    
    class Meta:
        verbose_name = "SubCategory"
        verbose_name_plural = "SubCategories"
        ordering = ['name']
        
    def __str__(self):
        return f"Category: {self.category.name} - Sub category: {self.name}"
    
class Product(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', blank=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
        unique_together = ('subcategory', 'name')
        
    def __str__(self):
        return self.name
