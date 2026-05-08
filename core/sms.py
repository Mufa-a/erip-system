import ssl
import africastalking
from decouple import config

# Fix for Python 3.14 strict SSL
ssl.create_default_context = lambda *args, **kwargs: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

def initialize_at():
    africastalking.initialize(
        username=config('AT_USERNAME', default='sandbox'),
        api_key=config('AT_API_KEY', default='')
    )
    return africastalking.SMS


def send_sms(phone, message):
    try:
        if phone.startswith('0'):
            phone = '+254' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+254' + phone

        sms = initialize_at()
        response = sms.send(message, [phone])
        print(f"SMS sent: {response}")
        return True
    except Exception as e:
        print(f"SMS error: {e}")
        return False


def initialize_at():
    africastalking.initialize(
        username=config('AT_USERNAME', default='sandbox'),
        api_key=config('AT_API_KEY', default='')
    )
    return africastalking.SMS


def send_sms(phone, message):
    try:
        # Format phone for Kenya
        if phone.startswith('0'):
            phone = '+254' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+254' + phone

        sms = initialize_at()
        response = sms.send(message, [phone])
        print(f"SMS sent: {response}")
        return True
    except Exception as e:
        print(f"SMS error: {e}")
        return False


def send_payment_sms(payment):
    customer = payment.invoice.customer
    phone    = customer.phone
    currency = 'KES'

    if not phone:
        return False

    message = (
        f"Dear {customer.name}, payment of "
        f"{currency} {payment.amount:,.2f} received. "
        f"Invoice #{payment.invoice.invoice_number}. "
        f"Balance: {currency} {payment.invoice.balance_due:,.2f}. "
        f"Thank you!"
    )
    return send_sms(phone, message)


def send_invoice_sms(invoice):
    customer = invoice.customer
    phone    = customer.phone
    currency = 'KES'

    if not phone:
        return False

    message = (
        f"Dear {customer.name}, invoice "
        f"#{invoice.invoice_number} of "
        f"{currency} {invoice.total:,.2f} created. "
        f"Due: {invoice.due_date}. "
        f"Please pay on time. Thank you!"
    )
    return send_sms(phone, message)


def send_low_stock_sms(product, admin_phone):
    if not admin_phone:
        return False

    message = (
        f"STOCK ALERT: {product.name} "
        f"(SKU: {product.sku}) is running low. "
        f"Current stock: {product.stock}. "
        f"Please reorder soon."
    )
    return send_sms(admin_phone, message)