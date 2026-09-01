from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Agent, InviteCode, PhoneOTP, User


class AgentInline(admin.StackedInline):
    model = Agent
    fk_name = "user"
    extra = 0
    max_num = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "phone", "profile_completed", "is_active"]
    list_filter = ["profile_completed", "is_staff", "is_active"]
    inlines = [AgentInline]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("EasyPro", {"fields": ("phone", "avatar", "profile_completed")}),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ["phone", "code", "created_at", "expires_at", "attempts", "is_used"]
    list_filter = ["is_used"]
    search_fields = ["phone"]
    readonly_fields = ["created_at"]


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        "get_display_label",
        "agent_type",
        "organization",
        "membership_status",
        "user",
        "is_verified",
        "is_active",
    ]
    list_filter = ["agent_type", "membership_status", "is_verified", "is_active"]
    search_fields = ["display_name", "company_name", "phone", "slug"]
    prepopulated_fields = {"slug": ("display_name", "company_name")}


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "organization",
        "uses_count",
        "max_uses",
        "expires_at",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "organization"]
    search_fields = ["code", "note", "organization__company_name"]
    readonly_fields = ["uses_count", "created_at", "updated_at"]
