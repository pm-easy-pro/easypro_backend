from datetime import timedelta

from django.db import models
from django.utils import timezone

from accounts.models import Agent
from common.models import BaseModel


class SubscriptionPackage(BaseModel):
    BILLING_MONTHLY = "monthly"
    BILLING_YEARLY = "yearly"
    BILLING_CHOICES = [
        (BILLING_MONTHLY, "Сар бүр"),
        (BILLING_YEARLY, "Жил бүр"),
    ]

    TARGET_INDIVIDUAL = "individual"
    TARGET_ORGANIZATION = "organization"
    TARGET_CHOICES = [
        (TARGET_INDIVIDUAL, "Хувь хүн агент"),
        (TARGET_ORGANIZATION, "Байгууллага"),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    billing_period = models.CharField(
        max_length=20, choices=BILLING_CHOICES, default=BILLING_MONTHLY
    )
    max_listings = models.PositiveIntegerField(default=5)
    max_vip_listings = models.PositiveIntegerField(default=0)
    features = models.JSONField(default=list, blank=True)
    is_popular = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "price"]
        verbose_name = "Багц"
        verbose_name_plural = "Багцууд"

    def __str__(self):
        return self.name

    def get_period_days(self):
        return 365 if self.billing_period == self.BILLING_YEARLY else 30


class Subscription(BaseModel):
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"
    STATUS_TRIAL = "trial"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Идэвхтэй"),
        (STATUS_CANCELLED, "Цуцлагдсан"),
        (STATUS_EXPIRED, "Дууссан"),
        (STATUS_TRIAL, "Туршилт"),
    ]

    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    package = models.ForeignKey(
        SubscriptionPackage,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True
    )
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Захиалга"
        verbose_name_plural = "Захиалгууд"

    def __str__(self):
        return f"{self.agent} — {self.package.name}"

    @property
    def is_valid(self):
        return self.status in (self.STATUS_ACTIVE, self.STATUS_TRIAL) and self.expires_at > timezone.now()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.started_at + timedelta(days=self.package.get_period_days())
        super().save(*args, **kwargs)

    @classmethod
    def get_active_for_agent(cls, agent):
        now = timezone.now()
        return (
            cls.objects.filter(
                agent=agent,
                status__in=[cls.STATUS_ACTIVE, cls.STATUS_TRIAL],
                expires_at__gt=now,
            )
            .select_related("package")
            .order_by("-expires_at")
            .first()
        )
