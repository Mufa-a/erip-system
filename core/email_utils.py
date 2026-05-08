from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_invoice_email(invoice):
    subject = f'Invoice #{invoice.invoice_number} from ERP System'
    message = f"""
Dear {invoice.customer.name},

Please find your invoice details below:

Invoice Number : {invoice.invoice_number}
Issue Date     : {invoice.issue_date}
Due Date       : {invoice.due_date}
Total Amount   : KES {invoice.total:,.2f}
Balance Due    : KES {invoice.balance_due:,.2f}

Please make payment before the due date.

Thank you for your business!

ERP System
"""
    if invoice.customer.email:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invoice.customer.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    return False


def send_payment_confirmation(payment):
    subject = f'Payment Confirmation - KES {payment.amount}'
    message = f"""
Dear {payment.invoice.customer.name},

We have received your payment. Details below:

Invoice        : #{payment.invoice.invoice_number}
Amount Paid    : KES {payment.amount:,.2f}
Payment Method : {payment.get_method_display()}
Reference      : {payment.reference or 'N/A'}
Date           : {payment.payment_date}
Balance Due    : KES {payment.invoice.balance_due:,.2f}

Thank you for your payment!

ERP System
"""
    if payment.invoice.customer.email:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.invoice.customer.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    return False


def send_low_stock_alert(products):
    if not products:
        return
    subject = '⚠ Low Stock Alert - ERP System'
    items   = '\n'.join([
        f"- {p.name} (SKU: {p.sku}) — Stock: {p.stock} (Alert: {p.low_stock_alert})"
        for p in products
    ])
    message = f"""
STOCK ALERT

The following products are running low:

{items}

Please reorder soon.

ERP System
"""
    from_email = settings.DEFAULT_FROM_EMAIL
    if from_email and from_email != 'noreply@erp.com':
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[from_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Stock alert email error: {e}")