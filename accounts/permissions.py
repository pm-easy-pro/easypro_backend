from django.db.models import Q
from rest_framework import permissions

from .models import Agent


def _scopes_contains(scope: str):
    """JSONField list contains a single string value."""
    return Q(visibility_scopes__contains=scope)


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


def public_properties_queryset():
    """Catalog on easypro.mn — active + public scope."""
    from properties.models import Property

    return (
        Property.objects.filter(is_active=True, status="active")
        .filter(_scopes_contains(Property.VIS_PUBLIC))
        .select_related("location", "agent", "agent__organization", "posted_by")
    )


def user_can_view_property(user, prop) -> bool:
    """Public listings are visible to all; internal scopes require portal role."""
    from properties.models import Property

    scopes = prop.visibility_scopes or []
    if Property.VIS_PUBLIC in scopes and prop.is_active and prop.status == "active":
        return True
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if user_can_manage_property(user, prop):
        return True

    org = get_company_admin_org(user)
    profile = getattr(user, "agent_profile", None)
    viewer_org_id = None
    if org:
        viewer_org_id = org.id
    elif (
        profile
        and profile.agent_type == Agent.TYPE_INDIVIDUAL
        and profile.organization_id
        and profile.membership_status == Agent.MEMBERSHIP_APPROVED
    ):
        viewer_org_id = profile.organization_id

    if Property.VIS_NETWORK in scopes and (
        org or (profile and profile.agent_type == Agent.TYPE_INDIVIDUAL)
    ):
        return True

    if Property.VIS_COMPANY in scopes and viewer_org_id:
        agent = prop.agent
        if agent and (
            agent.id == viewer_org_id
            or agent.organization_id == viewer_org_id
        ):
            return True

    return False


def portal_internal_feed_queryset(user):
    """
    Listings visible inside agent/company portals beyond own manage scope:
    network (all portal users) OR company (same org) OR own/manageable.
    """
    from properties.models import Property

    base = Property.objects.filter(is_active=True).select_related(
        "location", "agent", "agent__organization", "posted_by"
    )
    if not user or not user.is_authenticated:
        return base.none()
    if user.is_staff:
        return base

    managed = scoped_properties_queryset(user)
    org = get_company_admin_org(user)
    profile = getattr(user, "agent_profile", None)
    viewer_org_id = None
    if org:
        viewer_org_id = org.id
    elif (
        profile
        and profile.agent_type == Agent.TYPE_INDIVIDUAL
        and profile.organization_id
        and profile.membership_status == Agent.MEMBERSHIP_APPROVED
    ):
        viewer_org_id = profile.organization_id

    q = Q(pk__in=managed.values("pk")) | _scopes_contains(Property.VIS_NETWORK)
    if viewer_org_id:
        q |= (
            _scopes_contains(Property.VIS_COMPANY)
            & (
                Q(agent_id=viewer_org_id)
                | Q(agent__organization_id=viewer_org_id)
            )
        )
    return base.filter(q).distinct()
