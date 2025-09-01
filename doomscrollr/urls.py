from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.core.management import call_command

def run_migrations(request):
    # Run Django migrations
    call_command('migrate')
    return HttpResponse("✅ Migrations applied successfully!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),  # ✅ add this if not there
    path('api/auth/', include('dj_rest_auth.urls')),  # login/logout
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # register
    path("run-migrations/", run_migrations),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
