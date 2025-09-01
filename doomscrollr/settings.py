from django.contrib import admin
from django.urls import path, include
from django.core.management import call_command
from django.http import HttpResponse
from django.contrib.auth import get_user_model

# Run migrations safely
def run_migrations(request):
    try:
        call_command("makemigrations", "projects")
        call_command("migrate")
        return HttpResponse("✅ Migrations applied successfully")
    except Exception as e:
        return HttpResponse(f"❌ Migration error: {e}")

# Check if a superuser exists
def check_superuser(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("✅ A superuser already exists.")
    else:
        return HttpResponse("❌ No superuser found.")

# Create a default superuser (only if none exists)
def create_superuser(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("⚠️ Superuser already exists.")
    else:
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123"
        )
        return HttpResponse("✅ Superuser created (username: admin, password: adminpassword123)")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),

    # Maintenance helpers (remove later for security)
    path('run-migrations/', run_migrations),
    path('check-superuser/', check_superuser),
    path('create-superuser/', create_superuser),
]
