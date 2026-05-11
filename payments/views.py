# payments/views.py
# ============================================================
# Updated payment_add view to:
# 1. Fetch MpesaSettings from the current company
# 2. Pass company credentials directly to stk_push()
# 3. Show clear error if M-Pesa is not configured for this company
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Payment
from sales.models import Invoice
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def payment_list(request):
    payments = Payment.objects.select_related(
        'invoice__customer'
    ).order_by('-created_at')
    if request.company:
        payments = payments.filter(company=request.company)
    return render(request, 'payments/payment_list.html', {'payments': payments})


@login_required
def payment_add(request):
    invoices = Invoice.objects.exclude(
        status='paid'
    ).select_related('customer')
    if request.company:
        invoices = invoices.filter(company=request.company)

    if request.method == 'POST':
        invoice_id   = request.POST.get('invoice')
        amount       = request.POST.get('amount')
        method       = request.POST.get('method')
        reference    = request.POST.get('reference', '')
        payment_date = request.POST.get('payment_date')
        notes        = request.POST.get('notes', '')
        phone        = request.POST.get('phone', '')

        invoice = get_object_or_404(Invoice, pk=invoice_id)

        # ── M-Pesa STK Push ───────────────────────────────────
        if method == 'mpesa' and phone:
            try:
                from core.mpesa import stk_push
                from company.models import MpesaSettings

                # Fetch this company's M-Pesa settings
                mpesa_cfg = MpesaSettings.objects.filter(
                    company=request.company
                ).first()

                # Check M-Pesa is configured and enabled for this company
                if not mpesa_cfg or not mpesa_cfg.is_configured:
                    messages.error(
                        request,
                        'M-Pesa is not configured for your company. '
                        'Go to Company Settings → M-Pesa to set up your credentials.'
                    )
                    return render(request, 'payments/payment_form.html', {
                        'invoices': invoices,
                        'today':    timezone.now().date(),
                    })

                amount_int = int(float(amount))  # '551.99' → 552

                # Pass company credentials directly — no global .env keys used
                result = stk_push(
                    phone_number      = phone,
                    amount            = amount_int,
                    account_reference = f"INV-{invoice.invoice_number}",
                    description       = f"Payment for Invoice {invoice.invoice_number}",
                    consumer_key      = mpesa_cfg.consumer_key,      # decrypted automatically
                    consumer_secret   = mpesa_cfg.consumer_secret,   # decrypted automatically
                    shortcode         = mpesa_cfg.shortcode,
                    passkey           = mpesa_cfg.passkey,            # decrypted automatically
                    callback_url      = mpesa_cfg.callback_url,
                    env               = mpesa_cfg.environment,
                )

                if result.get('ResponseCode') == '0':
                    messages.success(
                        request,
                        f'M-Pesa prompt sent to {phone}! Enter PIN to complete.'
                    )
                    # Save CheckoutRequestID as reference so callback can match it
                    reference = result.get('CheckoutRequestID', reference)
                else:
                    error_msg = result.get('errorMessage') or result.get('ResponseDescription', 'Unknown error')
                    messages.warning(request, f"M-Pesa: {error_msg}")
                    logger.warning(f"STK Push failed for company {request.company}: {result}")

            except Exception as e:
                logger.error(f"M-Pesa STK Push exception: {e}")
                messages.warning(request, f'M-Pesa error: {str(e)}. Recording payment manually.')

        # ── Save payment record regardless of M-Pesa result ──
        Payment.objects.create(
            invoice      = invoice,
            amount       = amount,
            method       = method,
            reference    = reference,
            payment_date = payment_date,
            notes        = notes,
            company      = request.company,
        )

        # Update invoice status based on balance
        balance = invoice.balance_due
        if balance <= Decimal('0'):
            invoice.status = Invoice.Status.PAID
        elif balance < invoice.total:
            invoice.status = Invoice.Status.PARTIAL
        else:
            invoice.status = Invoice.Status.DRAFT
        invoice.save()

        messages.success(request, f'Payment of KES {amount} recorded!')

        # ── Optional: SMS notification ────────────────────────
        try:
            from core.sms import send_payment_sms
            payment_obj = Payment.objects.filter(
                invoice=invoice
            ).order_by('-created_at').first()
            if payment_obj and send_payment_sms(payment_obj):
                messages.info(request, f'SMS sent to {invoice.customer.phone}!')
        except Exception:
            pass

        # ── Optional: Email confirmation ──────────────────────
        try:
            from core.email_utils import send_payment_confirmation
            payment_obj = Payment.objects.filter(
                invoice=invoice
            ).order_by('-created_at').first()
            if payment_obj:
                send_payment_confirmation(payment_obj)
        except Exception:
            pass

        return redirect('payment_list')

    return render(request, 'payments/payment_form.html', {
        'invoices': invoices,
        'today':    timezone.now().date(),
    })


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted.')
        return redirect('payment_list')
    return render(request, 'payments/payment_confirm_delete.html', {
        'payment': payment
    })


@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom posts the STK Push result here.
    Matches by CheckoutRequestID and updates the payment reference.
    """
    if request.method == 'POST':
        try:
            data        = json.loads(request.body)
            result      = data.get('Body', {}).get('stkCallback', {})
            result_code = result.get('ResultCode')
            checkout_id = result.get('CheckoutRequestID')

            logger.info(f"M-Pesa callback received | checkout_id={checkout_id} | result_code={result_code}")

            if result_code == 0:
                # Payment successful — extract M-Pesa receipt number
                metadata  = result.get('CallbackMetadata', {}).get('Item', [])
                mpesa_ref = next(
                    (i['Value'] for i in metadata if i['Name'] == 'MpesaReceiptNumber'),
                    None
                )
                # Update the payment record with the real M-Pesa receipt
                updated = Payment.objects.filter(reference=checkout_id).update(
                    reference=mpesa_ref or checkout_id
                )
                logger.info(f"M-Pesa callback: updated {updated} payment(s) with ref {mpesa_ref}")
            else:
                desc = result.get('ResultDesc', 'Unknown')
                logger.warning(f"M-Pesa callback: payment failed | checkout_id={checkout_id} | reason={desc}")

        except Exception as e:
            logger.error(f"M-Pesa callback processing error: {e}")

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})