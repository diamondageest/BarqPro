from base64 import b64encode
import qrcode
import io


# def generate_qrcode(organization, tax_number, timestamp, invoice_total, tax_amount):
def generate_qrcode(invoice):
    # Invoice Data
    organization = invoice.account.organization
    tax_number = invoice.account.tax_number
    timestamp = str(invoice.created_at)
    invoice_total = str(invoice.total_after_vat)
    tax_amount = str(invoice.vat_amount)

    # Define TLV tags
    TLV_TAGS = {
        "seller_name": 1,
        "vat_number": 2,
        "invoice_date": 3,
        "invoice_total": 4,
        "vat_amount": 5,
    }

    # Create TLV-encoded data
    tlv_data = []

    # Seller Name (Tag 1)
    seller_name = organization.encode("utf-8")
    tlv_data.append(bytes([TLV_TAGS["seller_name"]]))  # Tag
    tlv_data.append(bytes([len(seller_name)]))  # Length
    tlv_data.append(seller_name)  # Value

    # VAT Number (Tag 2)
    vat_number = tax_number.encode("utf-8")
    tlv_data.append(bytes([TLV_TAGS["vat_number"]]))  # Tag
    tlv_data.append(bytes([len(vat_number)]))  # Length
    tlv_data.append(vat_number)  # Value

    # Invoice Date (Tag 3)
    invoice_date = timestamp.encode("utf-8")
    tlv_data.append(bytes([TLV_TAGS["invoice_date"]]))  # Tag
    tlv_data.append(bytes([len(invoice_date)]))  # Length
    tlv_data.append(invoice_date)  # Value

    # Invoice Total (Tag 4)
    invoice_total = invoice_total.encode("utf-8")
    tlv_data.append(bytes([TLV_TAGS["invoice_total"]]))  # Tag
    tlv_data.append(bytes([len(invoice_total)]))  # Length
    tlv_data.append(invoice_total)  # Value

    # VAT Amount (Tag 5)
    vat_amount = tax_amount.encode("utf-8")
    tlv_data.append(bytes([TLV_TAGS["vat_amount"]]))  # Tag
    tlv_data.append(bytes([len(vat_amount)]))  # Length
    tlv_data.append(vat_amount)  # Value

    # Combine all TLV data into a single byte string
    combined_data = b"".join(tlv_data)

    # Encode the combined data into Base64
    encoded_data = b64encode(combined_data).decode("utf-8")

    return encoded_data


def create_qrcode_image(qrcode_str, output_file="qrcode.png"):
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qrcode_str)
    qr.make(fit=True)

    # Generate QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code image to an in-memory buffer
    buffer = io.BytesIO()
    qr_image.save(buffer, format="PNG")  # Save as PNG
    buffer.seek(0)  # Move to the beginning of the buffer

    # Encode the image data as Base64
    image_base64 = b64encode(buffer.getvalue()).decode("utf-8")

    # Return the image as a data URI
    return f"data:image/png;base64,{image_base64}"
