from django.db import models

from common.models import BaseModel


class Location(BaseModel):
    DISTRICT_CHOICES = [
        ("baganuur", "Багануур"),
        ("bagakhangai", "Багахангай"),
        ("bayangol", "Баянгол"),
        ("bayanzurkh", "Баянзүрх"),
        ("khan_uul", "Хан-Уул"),
        ("nalaikh", "Налайх"),
        ("songinokhairkhan", "Сонгинохайрхан"),
        ("sukhbaatar", "Сүхбаатар"),
        ("chingeltei", "Чингэлтэй"),
        ("hud", "Хан-Уул дүүрэг (ХУД)"),
    ]

    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, db_index=True)
    official_address = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["district", "official_address"]
        verbose_name = "Байршил"
        verbose_name_plural = "Байршилууд"

    def __str__(self):
        return self.official_address


class LocationAlias(BaseModel):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["location", "name"]]
        verbose_name = "Байршлын нэр"
        verbose_name_plural = "Байршлын нэрүүд"

    def __str__(self):
        return f"{self.name} → {self.location.official_address}"
