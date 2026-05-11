import requests
import base64
import logging
from datetime import datetime
from decouple import config

# ============================================================
# mpesa.py
# All M-Pesa Daraja API calls live here.
# Logging added so errors show up in Render's log viewer.
# ============================================================

logger = logging.getLogger(__name__)


def get_mpesa_token():
    """
    Fetches a short-lived OAuth token from Safaricom.
    Uses sandbox or production URL based on MPESA_ENV setting.
    """
    consumer_key    = config('MPESA_CONSUMER_KEY',    default='')
    consumer_secret = config('MPESA_CONSUMER_SECRET', default='')
    env             = config('MPESA_ENV',             default='sandbox')

    # Guard: if credentials are missing, fail early with a clear message
    if not consumer_key or not consumer_secret:
        logger.error("MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET is not set!")
        raise ValueError("M-Pesa credentials are not configured. Check environment variables.")

    if env == 'production':
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    logger.info(f"Getting M-Pesa token from: {url}")

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode()

    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Basic {credentials}'},
            timeout=30  # ✅ Prevent hanging on Render
        )
        data  = response.json()
        token = data.get('access_token')

        if not token:
            # Log the full response so you can see Safaricom's error message
            logger.error(f"Failed to get M-Pesa token. Response: {data}")
            raise ValueError(f"Could not get M-Pesa token: {data}")

        logger.info("M-Pesa token fetched successfully.")
        return token

    except requests.RequestException as e:
        logger.error(f"M-Pesa token request failed: {e}")
        raise


def stk_push(phone_number, amount, account_reference, description):
    """
    Initiates an STK Push (Lipa Na M-Pesa Online).
    Returns the full Safaricom response as a dict.
    """
    env       = config('MPESA_ENV',          default='sandbox')
    shortcode = config('MPESA_SHORTCODE',    default='')
    passkey   = config('MPESA_PASSKEY',      default='')
    callback  = config('MPESA_CALLBACK_URL', default='')

    # Guard: log what values we're working with (mask sensitive ones)
    logger.info(f"STK Push | env={env} | shortcode={shortcode} | callback={callback} | phone={phone_number} | amount={amount}")

    if not callback:
        logger.error("MPESA_CALLBACK_URL is not set! STK Push will fail.")
        raise ValueError("MPESA_CALLBACK_URL is not configured.")

    if not passkey:
        logger.error("MPESA_PASSKEY is not set!")
        raise ValueError("MPESA_PASSKEY is not configured.")

    if env == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

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
        'Content-Type':  'application/json',
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

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data     = response.json()
        logger.info(f"STK Push response: {data}")
        return data

    except requests.RequestException as e:
        logger.error(f"STK Push request failed: {e}")
        raise


def check_transaction_status(checkout_request_id):
    """
    Queries the status of an STK Push transaction.
    Useful for confirming payment when callback is delayed.
    """
    env       = config('MPESA_ENV',       default='sandbox')
    shortcode = config('MPESA_SHORTCODE', default='')
    passkey   = config('MPESA_PASSKEY',   default='')

    if env == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    else:
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password  = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    token   = get_mpesa_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type':  'application/json',
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password':          password,
        'Timestamp':         timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data     = response.json()
        logger.info(f"Transaction status response: {data}")
        return data

    except requests.RequestException as e:
        logger.error(f"Transaction status check failed: {e}")
        raise