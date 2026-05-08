from django.db import models
from sales.models import Invoice
from company.models import Company


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH   = 'cash',   'Cash'
        BANK   = 'bank',   'Bank Transfer'
        MPESA  = 'mpesa',  'M-Pesa'
        CHEQUE = 'cheque', 'Cheque'
        CARD   = 'card',   'Card'

    company      = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='payments', null=True
    )
    invoice      = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='payments'
    )
    amount       = models.DecimalField(max_digits=12, decimal_places=2)
    method       = models.CharField(
        max_length=20, choices=Method.choices, default=Method.CASH
    )
    reference    = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KES {self.amount} via {self.get_method_display()}"