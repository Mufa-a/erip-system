import requests
import base64
from datetime import datetime
from decouple import config


def get_mpesa_token():
    consumer_key    = config('MPESA_CONSUMER_KEY')
    consumer_secret = config('MPESA_CONSUMER_SECRET')
    env             = config('MPESA_ENV', default='sandbox')

    if env == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode()

    response = requests.get(
        url,
        headers={'Authorization': f'Basic {credentials}'}
    )
    return response.json().get('access_token')


def stk_push(phone_number, amount, account_reference, description):
    env       = config('MPESA_ENV', default='sandbox')
    shortcode = config('MPESA_SHORTCODE')
    passkey   = config('MPESA_PASSKEY')
    callback  = config('MPESA_CALLBACK_URL')

    if env == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password  = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    # Format phone: 0712345678 → 254712345678
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+'):
        phone_number = phone_number[1:]

    token   = get_mpesa_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password':          password,
        'Timestamp':         timestamp,
        'TransactionType':   'CustomerPayBillOnline',
        'Amount':            int(amount),
        'PartyA':            phone_number,
        'PartyB':            shortcode,
        'PhoneNumber':       phone_number,
        'CallBackURL':       callback,
        'AccountReference':  account_reference,
        'TransactionDesc':   description,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def check_transaction_status(checkout_request_id):
    env       = config('MPESA_ENV', default='sandbox')
    shortcode = config('MPESA_SHORTCODE')
    passkey   = config('MPESA_PASSKEY')

    if env == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    else:
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password  = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    token   = get_mpesa_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password':          password,
        'Timestamp':         timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()