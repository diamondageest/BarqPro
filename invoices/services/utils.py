from invoices.models import Invoice, InvoiceHistory
from django.utils import timezone


def generate_invoice_uid(account, document_type="invoice"):
    """
    Generate the unique uid for the invoice
    """
    current_date = timezone.now().date()
    invoice_counter = Invoice.objects.filter(
        account=account, created_at__date=current_date
    ).count()
    # Extract the last two digits of the year
    year_last_two_digits = current_date.strftime("%y")

    # Format the month and day
    month_day = current_date.strftime("%m%d")

    # Create the invoice code by concatenating formatted date and invoice_counter
    if document_type == "offer":
        invoice_uid = f"OF{year_last_two_digits}{month_day}{invoice_counter}"
    else:
        invoice_uid = f"IN{year_last_two_digits}{month_day}{invoice_counter}"

    return invoice_uid


def create_invoice_history(invoice: Invoice, action_type="change_invoice_code"):
    """
    create an InvoiceHistory record for specific actions:
    - When the invoice code is changed from 'invoice' to 'credit'
    - When the invoice is rejected or error occurs

    params:
      - action_type: 'change_invoice_code' or 'reject_invoice'
    """

    # Create a history record for this invoice
    InvoiceHistory.objects.create(
        invoice=invoice,
        uid=invoice.uid,
        invoice_code=invoice.invoice_code,
        qrcode=invoice.qrcode,
        status=invoice.status,
        created_date=invoice.created_at,
        shared_date=invoice.shared_at,
        action_type=action_type,
        note=invoice.note,
    )
