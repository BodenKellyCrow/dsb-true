from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.management import call_command
from projects.models import UserProfile

# ✅ Admin profile fixer
def fix_admin_profile(request):
    try:
        User = get_user_model()
        admin_user = User.objects.get(username="admin")
        profile, created = UserProfile.objects.get_or_create(user=admin_user)
        if created:
            return HttpResponse("✅ Admin profile created successfully")
        else:
            return HttpResponse("⚠️ Admin profile already existed")
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

# ✅ Run migrations from browser
def run_migrations(request):
    try:
        call_command("makemigrations", "projects")
        call_command("migrate")
        return HttpResponse("✅ Migrations applied successfully")
    except Exception as e:
        return HttpResponse(f"❌ Migration error: {e}")

# ✅ Check if superuser exists
def check_superuser(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("✅ A superuser already exists.")
    else:
        return HttpResponse("❌ No superuser found.")

# ✅ Create a default superuser
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

# ✅ Import JWT views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Project app API
    path('api/', include('projects.urls')),  

    # dj-rest-auth endpoints
    path('api/auth/', include('dj_rest_auth.urls')),  
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  

    # JWT endpoints (needed for React frontend login/refresh)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # 🔧 Temporary helpers
    path("run-migrations/", run_migrations),
    path("check-superuser/", check_superuser),
    path("create-superuser/", create_superuser),
    path("fix-admin-profile/", fix_admin_profile),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
