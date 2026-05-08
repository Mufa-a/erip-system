from django.db import models
from company.models import Company


class Category(models.Model):
    company     = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='categories', null=True
    )
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Product(models.Model):
    company         = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='products', null=True
    )
    category        = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products'
    )
    name            = models.CharField(max_length=200)
    sku             = models.CharField(max_length=100)
    description     = models.TextField(blank=True)
    price           = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock           = models.PositiveIntegerField(default=0)
    low_stock_alert = models.PositiveIntegerField(default=10)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Stock: {self.stock})"

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_alert

    class Meta:
        unique_together = ('company', 'sku')