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

        if method == 'mpesa' and phone:
            try:
                from core.mpesa import stk_push
                amount_int = int(float(amount))  # ✅ '551.99' → 552
                result = stk_push(
                    phone_number=phone,
                    amount=amount_int,            # ✅ was: amount
                    account_reference=f"INV-{invoice.invoice_number}",
                    description=f"Payment for Invoice {invoice.invoice_number}"
                )
                if result.get('ResponseCode') == '0':
                    messages.success(
                        request,
                        f'M-Pesa prompt sent to {phone}! Enter PIN to complete.'
                    )
                    reference = result.get('CheckoutRequestID', reference)
                else:
                    messages.warning(
                        request,
                        f"M-Pesa: {result.get('errorMessage', 'Request sent')}"
                    )
            except Exception as e:
                messages.warning(request, f'M-Pesa error: {str(e)}. Recording manually.')

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method,
            reference=reference,
            payment_date=payment_date,
            notes=notes,
            company=request.company,
        )

        balance = invoice.balance_due
        if balance <= Decimal('0'):
            invoice.status = Invoice.Status.PAID
        elif balance < invoice.total:
            invoice.status = Invoice.Status.PARTIAL
        else:
            invoice.status = Invoice.Status.DRAFT
        invoice.save()

        messages.success(request, f'Payment of KES {amount} recorded!')

        try:
            from core.sms import send_payment_sms
            payment_obj = Payment.objects.filter(
                invoice=invoice
            ).order_by('-created_at').first()
            if payment_obj and send_payment_sms(payment_obj):
                messages.info(request, f'SMS sent to {invoice.customer.phone}!')
        except Exception:
            pass

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
    if request.method == 'POST':
        try:
            data        = json.loads(request.body)
            result      = data.get('Body', {}).get('stkCallback', {})
            result_code = result.get('ResultCode')
            checkout_id = result.get('CheckoutRequestID')

            if result_code == 0:
                metadata  = result.get('CallbackMetadata', {}).get('Item', [])
                mpesa_ref = next(
                    (i['Value'] for i in metadata if i['Name'] == 'MpesaReceiptNumber'),
                    None
                )
                Payment.objects.filter(reference=checkout_id).update(
                    reference=mpesa_ref or checkout_id
                )
        except Exception:
            pass

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})