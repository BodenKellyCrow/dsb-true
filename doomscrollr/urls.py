from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.management import call_command
from projects.models import UserProfile

# 🔧 Maintenance Utilities (safe to keep)
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

def run_migrations(request):
    try:
        call_command("makemigrations", "projects")
        call_command("migrate")
        return HttpResponse("✅ Migrations applied successfully")
    except Exception as e:
        return HttpResponse(f"❌ Migration error: {e}")

def check_superuser(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("✅ A superuser already exists.")
    else:
        return HttpResponse("❌ No superuser found.")

def fix_missing_profiles(request):
    User = get_user_model()
    created_count = 0
    for user in User.objects.all():
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            created_count += 1
    return HttpResponse(f"✅ Created {created_count} missing profiles.")


# JWT auth views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Project API
    path("api/", include("projects.urls")),

    # dj-rest-auth
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),

    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Maintenance helpers
    path("run-migrations/", run_migrations),
    path("check-superuser/", check_superuser),
    path("fix-admin-profile/", fix_admin_profile),
    path("fix-missing-profiles/", fix_missing_profiles),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
