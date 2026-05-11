# core/mpesa.py
# ============================================================
# M-Pesa Daraja API helper.
# Now accepts credentials as parameters instead of reading
# from .env — so each company uses their own keys.
# ============================================================

import requests
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_mpesa_token(consumer_key: str, consumer_secret: str, env: str = 'sandbox') -> str:
    """
    Fetches a short-lived OAuth bearer token from Safaricom Daraja.

    Args:
        consumer_key:    Company's Daraja consumer key (decrypted)
        consumer_secret: Company's Daraja consumer secret (decrypted)
        env:             'sandbox' or 'production'

    Returns:
        access_token string

    Raises:
        ValueError: if credentials are missing or token fetch fails
    """

    # Guard: fail early with a clear message if credentials are missing
    if not consumer_key or not consumer_secret:
        raise ValueError(
            "M-Pesa consumer_key or consumer_secret is missing. "
            "Please configure M-Pesa settings for this company."
        )

    # Choose correct Daraja URL based on environment
    if env == 'production':
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    logger.info(f"Fetching M-Pesa token | env={env}")

    # Base64 encode "consumer_key:consumer_secret"
    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode()

    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Basic {credentials}'},
            timeout=30  # prevent hanging on Render
        )
        data  = response.json()
        token = data.get('access_token')

        if not token:
            # Log full response so you can see Safaricom's error in Render logs
            logger.error(f"M-Pesa token fetch failed. Safaricom response: {data}")
            raise ValueError(f"Could not get M-Pesa access token: {data}")

        logger.info("M-Pesa token fetched successfully.")
        return token

    except requests.RequestException as e:
        logger.error(f"M-Pesa token request error: {e}")
        raise


def stk_push(
    phone_number:      str,
    amount:            int,
    account_reference: str,
    description:       str,
    consumer_key:      str,
    consumer_secret:   str,
    shortcode:         str,
    passkey:           str,
    callback_url:      str,
    env:               str = 'sandbox',
) -> dict:
    """
    Initiates an STK Push (Lipa Na M-Pesa Online) using the company's own credentials.

    Args:
        phone_number:      Customer phone. Accepts 07XX, +2547XX, 2547XX formats.
        amount:            Amount in KES (integer)
        account_reference: e.g. "INV-001"
        description:       e.g. "Payment for Invoice 001"
        consumer_key:      Company's decrypted consumer key
        consumer_secret:   Company's decrypted consumer secret
        shortcode:         Company's M-Pesa shortcode
        passkey:           Company's Lipa Na M-Pesa passkey
        callback_url:      Public HTTPS URL for Safaricom to POST the result to
        env:               'sandbox' or 'production'

    Returns:
        dict: Full Safaricom STK Push response
    """

    # Guard: validate all required credentials upfront
    missing = [
        name for name, val in [
            ('consumer_key',    consumer_key),
            ('consumer_secret', consumer_secret),
            ('shortcode',       shortcode),
            ('passkey',         passkey),
            ('callback_url',    callback_url),
        ] if not val
    ]
    if missing:
        raise ValueError(f"M-Pesa STK Push missing fields: {', '.join(missing)}")

    # Log what we're working with (never log actual credential values)
    logger.info(
        f"STK Push | env={env} | shortcode={shortcode} | "
        f"phone={phone_number} | amount={amount} | callback={callback_url}"
    )

    # Choose correct Daraja URL
    if env == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    # Build password: base64(shortcode + passkey + timestamp)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password  = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    # Normalize phone number to 2547XXXXXXXX format
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # Get fresh token using this company's credentials
    token   = get_mpesa_token(consumer_key, consumer_secret, env)
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
        'CallBackURL':       callback_url,
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


def check_transaction_status(
    checkout_request_id: str,
    consumer_key:        str,
    consumer_secret:     str,
    shortcode:           str,
    passkey:             str,
    env:                 str = 'sandbox',
) -> dict:
    """
    Queries the status of a pending STK Push transaction.
    Useful when the callback is delayed or missed.
    """

    if env == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    else:
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password  = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    token   = get_mpesa_token(consumer_key, consumer_secret, env)
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