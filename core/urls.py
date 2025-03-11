from django.urls import path
from .views import (
    home,
    privacy_policy,
    download_ios_app,
)
from django.contrib import admin
from django.urls import path
from invoices.models import Invoice


class CustomAdminSite(admin.AdminSite):
    site_header = "Fatoora Pro Admin Site"
    site_title = "Fatoora Pro Admin Site"


custom_admin_site = CustomAdminSite(name="customadmin")
custom_admin_site.register(Invoice)

urlpatterns = [
    path("", home, name="home"),
    path("download-ios/", download_ios_app, name="download_ios_app"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
]
