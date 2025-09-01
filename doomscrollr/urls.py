from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_superuser(request):
    User = get_user_model()
    username = "admin"
    email = "admin@example.com"
    password = "AdminPass123!"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        return HttpResponse("✅ Superuser created successfully!")
    else:
        return HttpResponse("⚠️ Superuser already exists.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),  # ✅ add this if not there
    path('api/auth/', include('dj_rest_auth.urls')),  # login/logout
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # register
    path("create-superuser/", create_superuser),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
