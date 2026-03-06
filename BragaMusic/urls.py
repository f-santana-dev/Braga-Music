# BragaMusic/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('instrumento.urls')),
]

# Em desenvolvimento e no modo demo do portfolio, habilita arquivos de media.
if settings.DEBUG or settings.SERVE_MEDIA_IN_PROD:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
