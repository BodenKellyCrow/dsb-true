from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.management import call_command

# ✅ Helper to run migrations from browser
def run_migrations(request):
    try:
        call_command("makemigrations", "projects")
        call_command("migrate")
        return HttpResponse("✅ Migrations applied successfully")
    except Exception as e:
        return HttpResponse(f"❌ Migration error: {e}")

# ✅ Helper to check if superuser exists
def check_superuser(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("✅ A superuser already exists.")
    else:
        return HttpResponse("❌ No superuser found.")

# ✅ Helper to create a superuser
def create_superuser(request):
    User = get_user_model()
    username = "admin"
    email = "admin@example.com"
    password = "AdminPass123!"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        return HttpResponse("✅ Superuser created successfully! (username: admin, password: AdminPass123!)")
    else:
        return HttpResponse("⚠️ Superuser already exists.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),  
    path('api/auth/', include('dj_rest_auth.urls')),  
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  

    # 🔧 Temporary helpers
    path("run-migrations/", run_migrations),
    path("check-superuser/", check_superuser),
    path("create-superuser/", create_superuser),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
