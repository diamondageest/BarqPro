from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path("", include("core.urls")),
    path("api/auth/", include("authentication.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/invoices/", include("invoices.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
