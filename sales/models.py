from django.db import models
from django.db.models import Sum
from customers.models import Customer
from products.models import Product
from accounts.models import User
from company.models import Company


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        SENT      = 'sent',      'Sent'
        PAID      = 'paid',      'Paid'
        PARTIAL   = 'partial',   'Partially Paid'
        OVERDUE   = 'overdue',   'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    company        = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='invoices', null=True
    )
    invoice_number = models.CharField(max_length=50)
    customer       = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='invoices'
    )
    created_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    status         = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    issue_date     = models.DateField(auto_now_add=True)
    due_date       = models.DateField()
    tax_rate       = models.DecimalField(max_digits=5, decimal_places=2, default=16)
    discount       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"INV-{self.invoice_number} | {self.customer.name}"

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def tax_amount(self):
        from decimal import Decimal
        return (self.subtotal - self.discount) * (self.tax_rate / 100)

    @property
    def total(self):
        return self.subtotal - self.discount + self.tax_amount

    @property
    def amount_paid(self):
        result = self.payments.aggregate(t=Sum('amount'))['t']
        return result or 0

    @property
    def balance_due(self):
        return self.total - self.amount_paid

    class Meta:
        unique_together = ('company', 'invoice_number')


class InvoiceItem(models.Model):
    invoice    = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='items'
    )
    product    = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.unit_price