from django.shortcuts import render
from django.contrib import messages
from invoices.models import Invoice
from invoices.services.utils import create_invoice_history
from django.shortcuts import redirect
from django.utils import timezone
from django.http import FileResponse


def home(request):
    return render(request, "home.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def download_ios_app(request):
    # Path to the IPA file in the static directory
    ipa_file_path = "staticfiles/ios/app.ipa"
    # Return the IPA file as a response
    return FileResponse(open(ipa_file_path, "rb"), as_attachment=True)
