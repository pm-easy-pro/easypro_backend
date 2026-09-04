from decimal import Decimal

from django.core.management.base import BaseCommand

from locations.data.master_locations import POPULAR_LOCATIONS, UB_DISTRICTS
from locations.models import Location, LocationAlias
from subscriptions.data.packages import PACKAGES
from subscriptions.models import SubscriptionPackage


class Command(BaseCommand):
    help = (
        "Production master data: УБ байршил, хороо, subscription багц. "
        "Demo зар/хэрэглэгч оруулахгүй."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-locations",
            action="store_true",
            help="Байршил seed хийхгүй",
        )
        parser.add_argument(
            "--skip-khoroo",
            action="store_true",
            help="Дүүргийн хороо seed хийхгүй (зөвхөн алдартай байршил)",
        )
        parser.add_argument(
            "--skip-packages",
            action="store_true",
            help="Subscription багц seed хийхгүй",
        )

    def handle(self, *args, **options):
        if not options["skip_locations"]:
            self._seed_locations(include_khoroo=not options["skip_khoroo"])
        if not options["skip_packages"]:
            self._seed_packages()

        self.stdout.write(self.style.SUCCESS("Master data амжилттай seed хийгдлээ."))
        self.stdout.write(f"  Байршил: {Location.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Alias: {LocationAlias.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Багц: {SubscriptionPackage.objects.filter(is_active=True).count()}")

    def _seed_locations(self, include_khoroo: bool):
        created = 0
        updated = 0
        alias_count = 0

        self.stdout.write("Алдартай байршил seed хийж байна...")
        for item in POPULAR_LOCATIONS:
            loc, was_created = Location.objects.update_or_create(
                official_address=item["official_address"],
                defaults={
                    "district": item["district"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

            for alias_name in item.get("aliases", []):
                _, alias_created = LocationAlias.objects.update_or_create(
                    location=loc,
                    name=alias_name,
                    defaults={"is_active": True},
                )
                if alias_created:
                    alias_count += 1

        if include_khoroo:
            self.stdout.write("УБ дүүргийн хороо seed хийж байна...")
            for district in UB_DISTRICTS:
                base_lat = district["latitude"]
                base_lng = district["longitude"]
                for n in range(1, district["khoroo_count"] + 1):
                    official_address = f"{district['label']}, {n}-р хороо"
                    # Дүүргийн төвөөс бага зэрэг тархуулах (map preview-д)
                    offset = Decimal(n % 10) * Decimal("0.001")
                    loc, was_created = Location.objects.update_or_create(
                        official_address=official_address,
                        defaults={
                            "district": district["district"],
                            "latitude": base_lat + offset,
                            "longitude": base_lng + offset,
                            "is_active": True,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Байршил: {created} шинэ, {updated} шинэчлэгдсэн, {alias_count} alias нэмэгдсэн"
            )
        )

    def _seed_packages(self):
        created = 0
        updated = 0

        self.stdout.write("Subscription багц seed хийж байна...")
        for data in PACKAGES:
            _, was_created = SubscriptionPackage.objects.update_or_create(
                slug=data["slug"],
                defaults={**data, "is_active": True},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Багц: {created} шинэ, {updated} шинэчлэгдсэн")
        )
