from django.db import models
from company.models import Company


class Supplier(models.Model):
    company    = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='suppliers', null=True
    )
    name       = models.CharField(max_length=200)
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20)
    address    = models.TextField(blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name