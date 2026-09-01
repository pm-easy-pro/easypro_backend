from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from common.models import BaseModel


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    profile_completed = models.BooleanField(
        default=False,
        help_text="OTP-өөр бүртгүүлсний дараа профайл бөглөсөн эсэх",
    )

    class Meta:
        verbose_name = "Хэрэглэгч"
        verbose_name_plural = "Хэрэглэгчид"


class PhoneOTP(models.Model):
    phone = models.CharField(max_length=8, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Утасны OTP"
        verbose_name_plural = "Утасны OTP"

    def __str__(self):
        return f"{self.phone} @ {self.created_at}"

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class Agent(BaseModel):
    TYPE_INDIVIDUAL = "individual"
    TYPE_ORGANIZATION = "organization"
    TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, "Хувь хүн"),
        (TYPE_ORGANIZATION, "Байгууллага"),
    ]

    MEMBERSHIP_PENDING = "pending"
    MEMBERSHIP_APPROVED = "approved"
    MEMBERSHIP_DENIED = "denied"
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_PENDING, "Хүлээгдэж буй"),
        (MEMBERSHIP_APPROVED, "Зөвшөөрсөн"),
        (MEMBERSHIP_DENIED, "Татгалзсан"),
    ]

    agent_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_profile",
    )
    organization = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_agents",
        limit_choices_to={"agent_type": TYPE_ORGANIZATION},
    )

    display_name = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    title = models.CharField(
        max_length=120,
        blank=True,
        help_text="Жишээ: Platinum agent, Senior broker",
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="agents/avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_verified = models.BooleanField(default=False)
    membership_status = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CHOICES,
        default=MEMBERSHIP_APPROVED,
        db_index=True,
    )
    invited_via = models.ForeignKey(
        "InviteCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registrations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_agent_memberships",
    )

    class Meta:
        ordering = ["display_name", "company_name"]
        verbose_name = "Агент"
        verbose_name_plural = "Агентүүд"

    def __str__(self):
        return self.get_display_label()

    @property
    def is_membership_approved(self) -> bool:
        if self.agent_type == self.TYPE_ORGANIZATION:
            return True
        if not self.organization_id:
            return self.membership_status == self.MEMBERSHIP_APPROVED
        return self.membership_status == self.MEMBERSHIP_APPROVED

    def get_display_label(self):
        if self.agent_type == self.TYPE_ORGANIZATION:
            return self.company_name or self.display_name or f"Agent #{self.pk}"
        return self.display_name or f"Agent #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.company_name if self.agent_type == self.TYPE_ORGANIZATION else self.display_name
            base = base or f"agent-{self.pk or ''}"
            self.slug = slugify(base)[:250] or f"agent-{self.pk}"
            if Agent.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{self.slug}-{self.pk or 'new'}"
        super().save(*args, **kwargs)


class InviteCode(BaseModel):
    organization = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="invite_codes",
        limit_choices_to={"agent_type": Agent.TYPE_ORGANIZATION},
    )
    code = models.CharField(max_length=32, unique=True, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_invite_codes",
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Хоосон бол хязгааргүй",
    )
    uses_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Урилгын код"
        verbose_name_plural = "Урилгын кодууд"

    def __str__(self):
        return f"{self.code} → {self.organization}"

    def is_redeemable(self) -> bool:
        if not self.is_active:
            return False
        if not self.organization_id or not self.organization.is_active:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False
        return True
