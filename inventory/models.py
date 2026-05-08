from django.db import models
from products.models import Product
from accounts.models import User
from company.models import Company


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN     = 'in',     'Stock In'
        OUT    = 'out',    'Stock Out'
        ADJUST = 'adjust', 'Adjustment'
        RETURN = 'return', 'Return'

    company       = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='stock_movements', null=True
    )
    product       = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity      = models.IntegerField()
    reference     = models.CharField(max_length=100, blank=True)
    notes         = models.TextField(blank=True)
    created_by    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} | {self.product.name} | {self.quantity}"