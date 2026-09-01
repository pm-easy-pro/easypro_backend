from django.db.models import Q
from rest_framework import permissions

from .models import Agent


class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAuthenticatedManageUser(permissions.BasePermission):
    """Logged-in users may hit manage APIs; queryset/object checks enforce scope."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


def get_company_admin_org(user):
    profile = getattr(user, "agent_profile", None)
    if (
        profile
        and profile.agent_type == Agent.TYPE_ORGANIZATION
        and profile.is_active
    ):
        return profile
    return None


def is_company_admin(user) -> bool:
    return get_company_admin_org(user) is not None


def scoped_properties_queryset(user):
    """
    Super admin: all properties.
    Company admin: listings for their company (org agent or member agents) + own posts.
    Owner / individual agent: only their own listings.
    """
    from properties.models import Property

    base = Property.objects.select_related(
        "location", "agent", "agent__organization", "posted_by"
    )
    if not user or not user.is_authenticated:
        return base.none()
    if user.is_staff:
        return base.all()

    org = get_company_admin_org(user)
    if org:
        return base.filter(
            Q(agent=org)
            | Q(agent__organization=org)
            | Q(posted_by=user)
        ).distinct()

    profile = getattr(user, "agent_profile", None)
    if profile and profile.agent_type == Agent.TYPE_INDIVIDUAL:
        return base.filter(Q(agent=profile) | Q(posted_by=user)).distinct()

    return base.filter(posted_by=user)


def user_can_manage_property(user, prop) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return scoped_properties_queryset(user).filter(pk=prop.pk).exists()


def scoped_agents_queryset(user):
    """
    Super admin: all individual agents.
    Company admin: only agents belonging to their company.
    Others: none.
    """
    qs = Agent.objects.filter(agent_type=Agent.TYPE_INDIVIDUAL).select_related(
        "organization", "user", "invited_via"
    )
    if not user or not user.is_authenticated:
        return qs.none()
    if user.is_staff:
        return qs
    org = get_company_admin_org(user)
    if org:
        return qs.filter(organization=org)
    return qs.none()


def can_manage_agents(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or is_company_admin(user)))
