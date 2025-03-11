DOCUMENT_TYPES = (
    ("invoice", "Invoice"),
    ("offer", "Offer"),
)

PAYMENT_METHODS = (
    ("10", "Cash"),
    ("30", "Credit"),
    ("42", "bank_account"),
    ("48", "bank_card"),
)

INVOICE_TYPES = (
    ("simplified", "Simplified"),
    ("standard", "Standard"),
)

INVOICE_CODE = (
    ("invoice", "Invoice"),
    ("credit", "credit"),
    ("debit", "debit"),
)

INVOICE_STATUS = (
    ("standby", "Standby"),
    # ("pending", "Pending"),
    ("passed", "Passed"),
    ("passed_with_warnings", "Passed with warnings"),
    ("rejected", "Rejected"),
    ("error", "Error"),
)

DISCOUNT_TYPES = (("amount", "Amount"), ("percentage", "Percentage"))

HISTORY_ACTION_TYPE = (
    ("change_invoice_code", "Change Invoice Code"),
    ("change_document_type", "Change Document Type"),
    ("reject_invoice", "Reject Invoice"),
)

CUSTOMER_INFO_REQUIRED = [
    "street",
    "city",
]

CUSTOMER_ZATCA_INFO_REQUIRED = [
    "building_number",
    "postal_zone",
    "district_name",
]
