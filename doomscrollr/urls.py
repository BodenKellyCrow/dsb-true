from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),  # ✅ add this if not there
    path('api/auth/', include('dj_rest_auth.urls')),  # login/logout
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # register
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
