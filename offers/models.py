from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Product(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to="products/", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    available = models.BooleanField(default=True)
    retailer_url = models.URLField(help_text="External website where coupon can be used")

    class Meta:
        ordering = ["name"]
        unique_together = ("subcategory", "name")

    def __str__(self):
        return self.name


class Coupon(models.Model):
    SINGLE_USE = "single"
    MULTI_USE = "multi"

    USAGE_CHOICES = [
        (SINGLE_USE, "Single Use"),
        (MULTI_USE, "Multi Use"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="coupons")
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True, help_text="Optional: describe the offer")
    discount_percent = models.PositiveIntegerField(blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_type = models.CharField(max_length=10, choices=USAGE_CHOICES, default=MULTI_USE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.code} ({self.product.name})"
