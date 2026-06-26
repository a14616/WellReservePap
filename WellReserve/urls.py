"""
URL configuration for WellReserve project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.views import pwa_manifest, pwa_service_worker

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('manifest.webmanifest', pwa_manifest, name='manifest'),
    path('sw.js', pwa_service_worker, name='service_worker'),
]

# Servir ficheiros media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
