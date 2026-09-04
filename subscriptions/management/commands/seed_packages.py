from django.core.management.base import BaseCommand

from subscriptions.data.packages import PACKAGES
from subscriptions.models import SubscriptionPackage


class Command(BaseCommand):
    help = "Subscription багцуудыг үүсгэнэ"

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for data in PACKAGES:
            _, was_created = SubscriptionPackage.objects.update_or_create(
                slug=data["slug"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Багц: {created} шинэ, {updated} шинэчлэгдсэн")
        )
