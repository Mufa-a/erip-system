from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from company.models import Company

User = get_user_model()


class Employee(models.Model):
    class Department(models.TextChoices):
        SALES      = 'sales',      'Sales'
        ACCOUNTS   = 'accounts',   'Accounts'
        OPERATIONS = 'operations', 'Operations'
        IT         = 'it',         'IT'
        HR         = 'hr',         'HR'
        MANAGEMENT = 'management', 'Management'

    class EmploymentType(models.TextChoices):
        FULLTIME = 'fulltime', 'Full Time'
        PARTTIME = 'parttime', 'Part Time'
        CONTRACT = 'contract', 'Contract'

    company         = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='employees', null=True
    )
    user            = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    employee_number = models.CharField(max_length=20, unique=True)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    email           = models.EmailField(blank=True)
    phone           = models.CharField(max_length=20)
    id_number       = models.CharField(max_length=20, blank=True)
    kra_pin         = models.CharField(max_length=20, blank=True)
    nssf_number     = models.CharField(max_length=20, blank=True)
    nhif_number     = models.CharField(max_length=20, blank=True)
    department      = models.CharField(max_length=20, choices=Department.choices)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULLTIME)
    basic_salary    = models.DecimalField(max_digits=12, decimal_places=2)
    hire_date       = models.DateField()
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Payroll(models.Model):
    class Status(models.TextChoices):
        DRAFT    = 'draft',    'Draft'
        APPROVED = 'approved', 'Approved'
        PAID     = 'paid',     'Paid'

    employee         = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    month            = models.DateField()
    basic_salary     = models.DecimalField(max_digits=12, decimal_places=2)
    allowances       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_salary     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paye             = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssf             = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nhif             = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.month.strftime('%B %Y')}"

    def calculate(self):
        basic = Decimal(str(self.basic_salary))
        allow = Decimal(str(self.allowances))
        over  = Decimal(str(self.overtime))
        other = Decimal(str(self.other_deductions))

        self.gross_salary = basic + allow + over

        self.nssf = min(basic * Decimal('0.06'), Decimal('2160'))

        gross = float(self.gross_salary)
        if gross <= 5999:    nhif = 150
        elif gross <= 7999:  nhif = 300
        elif gross <= 11999: nhif = 400
        elif gross <= 14999: nhif = 500
        elif gross <= 19999: nhif = 600
        elif gross <= 24999: nhif = 750
        elif gross <= 29999: nhif = 850
        elif gross <= 34999: nhif = 900
        elif gross <= 39999: nhif = 950
        elif gross <= 44999: nhif = 1000
        elif gross <= 49999: nhif = 1100
        elif gross <= 59999: nhif = 1200
        elif gross <= 69999: nhif = 1300
        elif gross <= 79999: nhif = 1400
        elif gross <= 89999: nhif = 1500
        elif gross <= 99999: nhif = 1600
        else:                nhif = 1700
        self.nhif = Decimal(str(nhif))

        taxable = float(self.gross_salary) - float(self.nssf)
        if taxable <= 24000:
            paye = taxable * 0.10
        elif taxable <= 32333:
            paye = 2400 + (taxable - 24000) * 0.25
        elif taxable <= 500000:
            paye = 4483 + (taxable - 32333) * 0.30
        elif taxable <= 800000:
            paye = 144553 + (taxable - 500000) * 0.325
        else:
            paye = 242053 + (taxable - 800000) * 0.35

        self.paye = Decimal(str(max(0, paye - 2400)))

        self.total_deductions = self.paye + self.nssf + self.nhif + other
        self.net_salary = self.gross_salary - self.total_deductions
        return self