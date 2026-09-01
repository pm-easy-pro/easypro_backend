from django.db import models

from common.models import BaseModel


class Property(BaseModel):
    LISTING_SELL = "sell"
    LISTING_RENT = "rent"
    LISTING_BUY = "buy"
    LISTING_CHOICES = [
        (LISTING_SELL, "Зарна"),
        (LISTING_RENT, "Түрээслүүлнэ"),
        (LISTING_BUY, "Авна"),
    ]

    PROPERTY_APARTMENT = "apartment"
    PROPERTY_HOUSE = "house"
    PROPERTY_OFFICE = "office"
    PROPERTY_COMMERCIAL = "commercial"
    PROPERTY_LAND = "land"
    PROPERTY_CHOICES = [
        (PROPERTY_APARTMENT, "Орон сууц"),
        (PROPERTY_HOUSE, "Гэр"),
        (PROPERTY_OFFICE, "Оффис"),
        (PROPERTY_COMMERCIAL, "Үйлчилгээний байр"),
        (PROPERTY_LAND, "Газар"),
    ]

    CONDITION_CHOICES = [
        ("new", "Шинэ"),
        ("excellent", "Маш сайн"),
        ("good", "Сайн"),
        ("fair", "Дундаж"),
        ("needs_renovation", "Засвар хэрэгтэй"),
    ]

    STATUS_CHOICES = [
        ("active", "Идэвхтэй"),
        ("pending", "Хүлээгдэж буй"),
        ("sold", "Зарагдсан"),
        ("rented", "Түрээслэгдсэн"),
        ("archived", "Архив"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()

    listing_type = models.CharField(max_length=20, choices=LISTING_CHOICES, db_index=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_CHOICES, db_index=True)

    building_type = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, db_index=True)

    district = models.CharField(max_length=50, db_index=True)
    official_address = models.CharField(max_length=255, db_index=True)
    unofficial_addresses = models.JSONField(default=list, blank=True)

    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
    )

    price = models.DecimalField(max_digits=14, decimal_places=0)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    room_count = models.PositiveSmallIntegerField(default=1)

    floor = models.SmallIntegerField(null=True, blank=True)
    total_floor = models.SmallIntegerField(null=True, blank=True)
    has_elevator = models.BooleanField(default=False)
    window_count = models.PositiveSmallIntegerField(null=True, blank=True)
    bathroom_count = models.PositiveSmallIntegerField(null=True, blank=True)

    VIEW_NORTH = "north"
    VIEW_SOUTH = "south"
    VIEW_EAST = "east"
    VIEW_WEST = "west"
    VIEW_NORTHEAST = "northeast"
    VIEW_NORTHWEST = "northwest"
    VIEW_SOUTHEAST = "southeast"
    VIEW_SOUTHWEST = "southwest"
    VIEW_PANORAMIC = "panoramic"
    VIEW_CITY = "city"
    VIEW_MOUNTAIN = "mountain"
    VIEW_COURTYARD = "courtyard"
    VIEW_DIRECTION_CHOICES = [
        ("", "Тодорхойгүй"),
        (VIEW_NORTH, "Хойд"),
        (VIEW_SOUTH, "Өмнөд"),
        (VIEW_EAST, "Зүүн"),
        (VIEW_WEST, "Баруун"),
        (VIEW_NORTHEAST, "Зүүн хойд"),
        (VIEW_NORTHWEST, "Баруун хойд"),
        (VIEW_SOUTHEAST, "Зүүн өмнөд"),
        (VIEW_SOUTHWEST, "Баруун өмнөд"),
        (VIEW_PANORAMIC, "Панорам"),
        (VIEW_CITY, "Хотын үзэсгэлэн"),
        (VIEW_MOUNTAIN, "Уулын үзэсгэлэн"),
        (VIEW_COURTYARD, "Дотоод талбай"),
    ]
    view_direction = models.CharField(
        max_length=20,
        choices=VIEW_DIRECTION_CHOICES,
        blank=True,
        default="",
        db_index=True,
    )

    garage = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)

    PAYMENT_PRIVATE_LEASE = "private_lease"
    PAYMENT_BANK_LOAN = "bank_loan"
    PAYMENT_CASH = "cash"
    PAYMENT_BARTER = "barter"
    PAYMENT_TERM_CHOICES = [
        (PAYMENT_PRIVATE_LEASE, "Хувь лизингээр авах боломжтой"),
        (PAYMENT_BANK_LOAN, "Банкны зээлээр авах боломжтой"),
        (PAYMENT_CASH, "Бэлэн төлөлтөөр зарах боломжтой"),
        (PAYMENT_BARTER, "Бартераар зарах боломжтой"),
    ]
    payment_terms = models.JSONField(default=list, blank=True)

    year_built = models.PositiveSmallIntegerField(null=True, blank=True)

    LAND_RIGHT_OWNERSHIP = "ownership"
    LAND_RIGHT_POSSESSION = "possession"
    LAND_RIGHT_USE = "use"
    LAND_RIGHT_CHOICES = [
        (LAND_RIGHT_OWNERSHIP, "Өмчлөх"),
        (LAND_RIGHT_POSSESSION, "Эзэмших"),
        (LAND_RIGHT_USE, "Ашиглах"),
    ]
    parcel_number = models.CharField(max_length=100, blank=True, default="")
    land_right_type = models.CharField(
        max_length=20,
        choices=LAND_RIGHT_CHOICES,
        blank=True,
        default="",
        db_index=True,
    )
    land_contract_start = models.DateField(null=True, blank=True)
    land_contract_end = models.DateField(null=True, blank=True)

    LAND_USE_SERVICE_APT = "service_apartment"
    LAND_USE_HOUSEHOLD = "household"
    LAND_USE_RESIDENTIAL_YARD = "residential_yard"
    LAND_USE_PRIVATE_RESIDENCE = "private_residence"
    LAND_USE_OTHER = "other"
    LAND_USE_CHOICES = [
        (LAND_USE_SERVICE_APT, "Үйлчилгээтэй орон сууц"),
        (LAND_USE_HOUSEHOLD, "Аж, ахуйн"),
        (LAND_USE_RESIDENTIAL_YARD, "Гэр, орон сууц хашааны газар"),
        (LAND_USE_PRIVATE_RESIDENCE, "Амины орон сууц"),
        (LAND_USE_OTHER, "Бусад"),
    ]
    land_use_type = models.CharField(
        max_length=30,
        choices=LAND_USE_CHOICES,
        blank=True,
        default="",
        db_index=True,
    )

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_vip = models.BooleanField(default=False)

    views_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)

    thumbnail = models.ImageField(upload_to="properties/thumbnails/", blank=True, null=True)
    images = models.JSONField(default=list, blank=True)

    LISTING_OWNER_OWNER = "owner"
    LISTING_OWNER_AGENT = "agent"
    LISTING_OWNER_COMPANY = "company"
    LISTING_OWNER_CHOICES = [
        (LISTING_OWNER_OWNER, "Эзэн"),
        (LISTING_OWNER_AGENT, "Агент"),
        (LISTING_OWNER_COMPANY, "Компани"),
    ]

    listing_owner_type = models.CharField(
        max_length=20,
        choices=LISTING_OWNER_CHOICES,
        default=LISTING_OWNER_OWNER,
        db_index=True,
    )
    agent = models.ForeignKey(
        "accounts.Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
    )
    posted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_properties",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Үл хөдлөх хөрөнгө"
        verbose_name_plural = "Үл хөдлөх хөрөнгүүд"

    def __str__(self):
        return self.title
