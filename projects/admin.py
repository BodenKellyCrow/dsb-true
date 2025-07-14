from django.contrib import admin
from .models import Project
from .models import Transaction
from .models import UserProfile

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'funding_goal', 'current_funding', 'created_at')
    search_fields = ('title', 'owner__username')
    list_filter = ('created_at',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'project', 'amount', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'project__title')
    list_filter = ('timestamp',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance')
    search_fields = ('user__username',)

