from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Agent
from locations.models import Location, LocationAlias
from properties.models import Property

User = get_user_model()


LOCATION_DATA = [
    {
        "district": "hud",
        "official_address": "ХУД 11-р хороо",
        "latitude": Decimal("47.886300"),
        "longitude": Decimal("106.905700"),
        "aliases": ["Зайсан толгой", "River Garden", "Зайсан", "Zaisan"],
    },
    {
        "district": "hud",
        "official_address": "Marshall Town",
        "latitude": Decimal("47.888100"),
        "longitude": Decimal("106.912400"),
        "aliases": ["Маршал таун", "Marshall"],
    },
    {
        "district": "hud",
        "official_address": "Bella Vista",
        "latitude": Decimal("47.884500"),
        "longitude": Decimal("106.918200"),
        "aliases": ["Белла Виста", "Bella"],
    },
    {
        "district": "bayanzurkh",
        "official_address": "Encanto",
        "latitude": Decimal("47.918600"),
        "longitude": Decimal("106.945300"),
        "aliases": ["Энканто", "Encanto Town"],
    },
    {
        "district": "bayanzurkh",
        "official_address": "Olympic Residence",
        "latitude": Decimal("47.921200"),
        "longitude": Decimal("106.938700"),
        "aliases": ["Олимпик резидэнс", "Olympic"],
    },
    {
        "district": "bayanzurkh",
        "official_address": "Tokyo Town",
        "latitude": Decimal("47.915800"),
        "longitude": Decimal("106.952100"),
        "aliases": ["Токио таун", "Tokyo"],
    },
    {
        "district": "bayanzurkh",
        "official_address": "Нарны хороолол",
        "latitude": Decimal("47.913400"),
        "longitude": Decimal("106.928900"),
        "aliases": ["Narnii Horoolol", "Нарны"],
    },
]

PAYMENT_TERM_POOLS = [
    ["cash", "bank_loan"],
    ["bank_loan", "barter"],
    ["cash"],
    ["private_lease", "cash"],
    ["private_lease", "bank_loan", "cash"],
    ["cash", "barter"],
    ["bank_loan"],
    ["private_lease"],
]


PROPERTY_TEMPLATES = [
    {
        "location_key": "ХУД 11-р хороо",
        "title": "River Garden — 3 өрөө, дээд давхар, Зайсан хараат",
        "listing_type": "sell",
        "property_type": "apartment",
        "price": 680_000_000,
        "area_m2": 98.5,
        "room_count": 3,
        "floor": 12,
        "total_floor": 15,
        "is_verified": True,
        "is_vip": True,
        "aliases_extra": ["River Garden", "Зайсан"],
    },
    {
        "location_key": "ХУД 11-р хороо",
        "title": "Зайсан толгойд 2 өрөө, шинэ засвар",
        "listing_type": "rent",
        "property_type": "apartment",
        "price": 2_800_000,
        "area_m2": 72.0,
        "room_count": 2,
        "floor": 8,
        "total_floor": 12,
        "furnished": True,
        "is_verified": True,
        "aliases_extra": ["Зайсан толгой", "Зайсан"],
    },
    {
        "location_key": "Marshall Town",
        "title": "Marshall Town 4 өрөө пентхаус",
        "listing_type": "sell",
        "property_type": "apartment",
        "price": 1_250_000_000,
        "area_m2": 145.0,
        "room_count": 4,
        "floor": 18,
        "total_floor": 20,
        "has_elevator": True,
        "window_count": 6,
        "bathroom_count": 2,
        "view_direction": "city",
        "garage": True,
        "balcony": True,
        "is_vip": True,
        "aliases_extra": ["Маршал таун"],
    },
    {
        "location_key": "Bella Vista",
        "title": "Bella Vista — 2 өрөө, гэрэл сайтай",
        "listing_type": "rent",
        "property_type": "apartment",
        "price": 2_200_000,
        "area_m2": 65.0,
        "room_count": 2,
        "floor": 6,
        "total_floor": 10,
        "has_elevator": True,
        "window_count": 4,
        "bathroom_count": 1,
        "view_direction": "south",
        "furnished": True,
        "aliases_extra": ["Белла Виста"],
    },
    {
        "location_key": "Encanto",
        "title": "Encanto хотхонд 3 өрөө орон сууц",
        "listing_type": "sell",
        "property_type": "apartment",
        "price": 520_000_000,
        "area_m2": 88.0,
        "room_count": 3,
        "floor": 5,
        "total_floor": 9,
        "has_elevator": True,
        "window_count": 5,
        "bathroom_count": 2,
        "view_direction": "east",
        "is_verified": True,
        "aliases_extra": ["Энканто"],
    },
    {
        "location_key": "Olympic Residence",
        "title": "Olympic Residence VIP 3 өрөө",
        "listing_type": "sell",
        "property_type": "apartment",
        "price": 890_000_000,
        "area_m2": 110.0,
        "room_count": 3,
        "floor": 14,
        "total_floor": 22,
        "has_elevator": True,
        "window_count": 7,
        "bathroom_count": 2,
        "view_direction": "panoramic",
        "is_vip": True,
        "is_verified": True,
        "aliases_extra": ["Олимпик"],
    },
    {
        "location_key": "Tokyo Town",
        "title": "Tokyo Town 1 өрөө студи",
        "listing_type": "rent",
        "property_type": "apartment",
        "price": 1_500_000,
        "area_m2": 38.0,
        "room_count": 1,
        "floor": 3,
        "total_floor": 8,
        "furnished": True,
        "aliases_extra": ["Токио таун"],
    },
    {
        "location_key": "Нарны хороолол",
        "title": "Нарны хороололд 2 өрөө, өмнөх цонхтой",
        "listing_type": "sell",
        "property_type": "apartment",
        "price": 380_000_000,
        "area_m2": 58.0,
        "room_count": 2,
        "floor": 4,
        "total_floor": 5,
        "aliases_extra": ["Narnii Horoolol"],
    },
    {
        "location_key": "ХУД 11-р хороо",
        "title": "Зайсан бүсийн 5 өрөө гэр",
        "listing_type": "sell",
        "property_type": "house",
        "price": 2_100_000_000,
        "area_m2": 280.0,
        "room_count": 5,
        "garage": True,
        "balcony": True,
        "aliases_extra": ["Зайсан"],
    },
    {
        "location_key": "Encanto",
        "title": "Encanto оффис 85 м²",
        "listing_type": "rent",
        "property_type": "office",
        "price": 3_500_000,
        "area_m2": 85.0,
        "room_count": 2,
        "floor": 2,
        "total_floor": 6,
        "aliases_extra": ["Encanto Town"],
    },
        {
            "location_key": "Olympic Residence",
            "title": "Olympic — 2 өрөө түрээс, тавилгатай",
            "listing_type": "rent",
            "property_type": "apartment",
            "price": 2_600_000,
            "area_m2": 68.0,
            "room_count": 2,
            "floor": 9,
            "total_floor": 22,
            "has_elevator": True,
            "furnished": True,
            "is_verified": True,
            "aliases_extra": ["Олимпик"],
        },
        {
            "location_key": "Marshall Town",
            "title": "Marshall Town оффис 120 м²",
            "listing_type": "rent",
            "property_type": "office",
            "price": 4_800_000,
            "area_m2": 120.0,
            "room_count": 3,
            "floor": 4,
            "total_floor": 12,
            "has_elevator": True,
            "aliases_extra": ["Маршал таун"],
        },
        {
            "location_key": "Bella Vista",
            "title": "Bella Vista 3 өрөө — зарж байна",
            "listing_type": "sell",
            "property_type": "apartment",
            "price": 610_000_000,
            "area_m2": 92.0,
            "room_count": 3,
            "floor": 7,
            "total_floor": 10,
            "has_elevator": True,
            "balcony": True,
            "is_vip": True,
            "aliases_extra": ["Белла Виста"],
        },
        {
            "location_key": "Tokyo Town",
            "title": "Tokyo Town худалдааны байр",
            "listing_type": "sell",
            "property_type": "commercial",
            "price": 780_000_000,
            "area_m2": 95.0,
            "room_count": 2,
            "floor": 1,
            "total_floor": 4,
            "aliases_extra": ["Токио таун"],
        },
        {
            "location_key": "Нарны хороолол",
            "title": "Нарны хороолол — газар 700 м²",
            "listing_type": "sell",
            "property_type": "land",
            "price": 450_000_000,
            "area_m2": 700.0,
            "room_count": 1,
            "parcel_number": "1700020123",
            "land_right_type": "ownership",
            "land_use_type": "residential_yard",
            "aliases_extra": ["Нарны"],
            "images": [
                "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80",
                "https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=800&q=80",
            ],
        },
]

IMAGE_POOL = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6162a56a0c?w=800&q=80",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80",
    "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&q=80",
    "https://images.unsplash.com/photo-1512917774080-999a1f42c235?w=800&q=80",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80",
    "https://images.unsplash.com/photo-1605276374101-dee0e788a243?w=800&q=80",
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80",
]


class Command(BaseCommand):
    help = "Seed Mongolian demo locations and properties"

    def handle(self, *args, **options):
        self.stdout.write("Seeding locations...")
        location_map = {}
        for item in LOCATION_DATA:
            loc, _ = Location.objects.update_or_create(
                official_address=item["official_address"],
                defaults={
                    "district": item["district"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "is_active": True,
                },
            )
            location_map[item["official_address"]] = loc
            for alias_name in item["aliases"]:
                LocationAlias.objects.update_or_create(
                    location=loc,
                    name=alias_name,
                    defaults={"is_active": True},
                )

        self.stdout.write("Seeding agents...")
        remax_org, _ = Agent.objects.update_or_create(
            slug="remax-hub",
            defaults={
                "agent_type": Agent.TYPE_ORGANIZATION,
                "company_name": "RE/MAX HUB",
                "phone": "7711-2000",
                "email": "hub@remax.mn",
                "address": "3rd floor, Encanto Mall, Bayanzurkh District, Ulaanbaatar, Mongolia, 13312",
                "bio": (
                    "+200 агенттай Монголын хамгийн том үл хөдлөх хөрөнгө зуучлалын брокер оффис. "
                    "Мэргэжлийн баг хамт олон, сэтгэл ханамжтай үйлчилгээг санал болгоно."
                ),
                "is_verified": True,
                "is_active": True,
            },
        )
        easypro_org, _ = Agent.objects.update_or_create(
            slug="easypro-realty",
            defaults={
                "agent_type": Agent.TYPE_ORGANIZATION,
                "company_name": "EasyPro Realty",
                "phone": "7711-2233",
                "email": "info@easypro.mn",
                "address": "Улаанбаатар, Сүхбаатар дүүрэг",
                "bio": "Монголын премиум үл хөдлөх хөрөнгийн зуучлал.",
                "is_verified": True,
                "is_active": True,
            },
        )
        marshall_org, _ = Agent.objects.update_or_create(
            slug="marshall-agency",
            defaults={
                "agent_type": Agent.TYPE_ORGANIZATION,
                "company_name": "Marshall Agency",
                "phone": "7711-4455",
                "email": "contact@marshall.mn",
                "address": "Улаанбаатар, Хан-Уул дүүрэг",
                "is_verified": True,
                "is_active": True,
            },
        )
        agent_ankhbileg, _ = Agent.objects.update_or_create(
            slug="ankhbileg-d",
            defaults={
                "agent_type": Agent.TYPE_INDIVIDUAL,
                "display_name": "Ankhbileg.D",
                "title": "Platinum agent",
                "organization": remax_org,
                "phone": "9911-5566",
                "email": "ankhbileg@remax.mn",
                "bio": "RE/MAX HUB-ийн Platinum агент.",
                "is_verified": True,
                "is_active": True,
            },
        )
        agent_bolormaa, _ = Agent.objects.update_or_create(
            slug="bolormaa-agent",
            defaults={
                "agent_type": Agent.TYPE_INDIVIDUAL,
                "display_name": "Б.Болормаа",
                "title": "Senior agent",
                "organization": easypro_org,
                "phone": "9911-2233",
                "email": "bolormaa@easypro.mn",
                "bio": "Зайсан, River Garden бүсийн мэргэжилтэн агент.",
                "is_verified": True,
                "is_active": True,
            },
        )
        agent_temuulen, _ = Agent.objects.update_or_create(
            slug="temuulen-agent",
            defaults={
                "agent_type": Agent.TYPE_INDIVIDUAL,
                "display_name": "Т.Тэмүүлэн",
                "title": "Agent",
                "organization": marshall_org,
                "phone": "9911-7788",
                "is_verified": True,
                "is_active": True,
            },
        )
        agent_independent, _ = Agent.objects.update_or_create(
            slug="batbayar-independent",
            defaults={
                "agent_type": Agent.TYPE_INDIVIDUAL,
                "display_name": "Б.Батбаяр",
                "title": "Independent agent",
                "phone": "8811-9900",
                "bio": "Бие даасан агент — Encanto, Olympic бүс.",
                "is_active": True,
            },
        )

        demo_user, _ = User.objects.get_or_create(
            username="demo_owner",
            defaults={"email": "owner@demo.mn", "first_name": "Бат", "last_name": "Эрдэнэ"},
        )
        demo_user.first_name = demo_user.first_name or "Бат"
        demo_user.last_name = demo_user.last_name or "Эрдэнэ"
        demo_user.phone = demo_user.phone or "9900-1122"
        demo_user.is_staff = False
        demo_user.is_superuser = False
        demo_user.set_password("demo1234")
        demo_user.save()

        # Company admin — RE/MAX HUB organization profile
        company_admin, _ = User.objects.get_or_create(
            username="demo_company_admin",
            defaults={
                "email": "admin@remaxhub.mn",
                "first_name": "RE/MAX",
                "last_name": "Admin",
            },
        )
        company_admin.first_name = "RE/MAX"
        company_admin.last_name = "Admin"
        company_admin.email = "admin@remaxhub.mn"
        company_admin.phone = company_admin.phone or "7711-2000"
        company_admin.is_staff = False
        company_admin.is_superuser = False
        company_admin.set_password("demo1234")
        company_admin.save()
        Agent.objects.filter(user=company_admin).exclude(pk=remax_org.pk).update(user=None)
        remax_org.user = company_admin
        remax_org.save(update_fields=["user"])

        # Individual agent under RE/MAX (approved member, NOT system admin)
        agent_user, _ = User.objects.get_or_create(
            username="demo_agent",
            defaults={"email": "agent@demo.mn", "first_name": "Ankhbileg", "last_name": "D"},
        )
        agent_user.first_name = "Ankhbileg"
        agent_user.last_name = "D"
        agent_user.email = agent_user.email or "agent@demo.mn"
        agent_user.is_staff = False
        agent_user.is_superuser = False
        agent_user.set_password("demo1234")
        agent_user.save()
        Agent.objects.filter(user=agent_user).exclude(pk=agent_ankhbileg.pk).update(user=None)
        agent_ankhbileg.user = agent_user
        agent_ankhbileg.organization = remax_org
        agent_ankhbileg.membership_status = Agent.MEMBERSHIP_APPROVED
        agent_ankhbileg.is_verified = True
        agent_ankhbileg.is_active = True
        agent_ankhbileg.save(
            update_fields=[
                "user",
                "organization",
                "membership_status",
                "is_verified",
                "is_active",
                "updated_at",
            ]
        )

        bolormaa_user, _ = User.objects.get_or_create(
            username="demo_agent_bolormaa",
            defaults={"email": "bolormaa@demo.mn", "first_name": "Болормаа", "last_name": "Б"},
        )
        bolormaa_user.first_name = bolormaa_user.first_name or "Болормаа"
        bolormaa_user.last_name = bolormaa_user.last_name or "Б"
        bolormaa_user.is_staff = False
        bolormaa_user.is_superuser = False
        bolormaa_user.set_password("demo1234")
        bolormaa_user.save()
        Agent.objects.filter(user=bolormaa_user).exclude(pk=agent_bolormaa.pk).update(user=None)
        agent_bolormaa.user = bolormaa_user
        agent_bolormaa.membership_status = Agent.MEMBERSHIP_APPROVED
        agent_bolormaa.save(update_fields=["user", "membership_status", "updated_at"])

        # Platform system admin — no agent company profile
        admin_user, _ = User.objects.get_or_create(
            username="demo_admin",
            defaults={
                "email": "admin@demo.mn",
                "first_name": "Platform",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.first_name = "Platform"
        admin_user.last_name = "Admin"
        admin_user.set_password("demo1234")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        # Ensure system admin is not tied to a company agent profile
        Agent.objects.filter(user=admin_user).update(user=None)

        owner_assignments = [
            Property.LISTING_OWNER_AGENT,
            Property.LISTING_OWNER_COMPANY,
            Property.LISTING_OWNER_OWNER,
            Property.LISTING_OWNER_AGENT,
        ]
        agent_cycle = [
            agent_ankhbileg,
            remax_org,
            None,
            agent_bolormaa,
            agent_temuulen,
            agent_independent,
            marshall_org,
            easypro_org,
        ]

        self.stdout.write("Seeding properties...")

        for idx, tmpl in enumerate(PROPERTY_TEMPLATES):
            loc = location_map[tmpl["location_key"]]
            aliases = list(
                LocationAlias.objects.filter(location=loc).values_list("name", flat=True)
            )
            unofficial = list(set(aliases + tmpl.get("aliases_extra", [])))
            images = tmpl.get("images") or [
                IMAGE_POOL[idx % len(IMAGE_POOL)],
                IMAGE_POOL[(idx + 1) % len(IMAGE_POOL)],
                IMAGE_POOL[(idx + 2) % len(IMAGE_POOL)],
            ]
            is_land = tmpl["property_type"] == "land"
            description = tmpl.get("description")
            if not description:
                if is_land:
                    description = (
                        f"{tmpl['title']} — EasyPro газрын зар. "
                        f"{loc.official_address} байршилд {tmpl['area_m2']} м² талбайтай газар."
                    )
                else:
                    description = (
                        f"{tmpl['title']} — EasyPro demo зар. {loc.official_address} байршилд "
                        f"байрлах {tmpl['room_count']} өрөөтэй, {tmpl['area_m2']} м² талбайтай "
                        "үл хөдлөх хөрөнгийн зар. Бүрэн тавилгатай, аюулгүй хороолол."
                    )
            owner_type = owner_assignments[idx % len(owner_assignments)]
            agent_ref = agent_cycle[idx % len(agent_cycle)]
            if owner_type == Property.LISTING_OWNER_OWNER:
                agent_ref = None
                posted = demo_user
            elif owner_type == Property.LISTING_OWNER_COMPANY:
                posted = demo_user
            else:
                posted = agent_user if agent_ref and agent_ref.agent_type == Agent.TYPE_INDIVIDUAL else demo_user

            Property.objects.update_or_create(
                title=tmpl["title"],
                defaults={
                    "description": description,
                    "listing_type": tmpl["listing_type"],
                    "property_type": tmpl["property_type"],
                    "building_type": "" if is_land else "Орон сууцны барилга",
                    "condition": "good" if is_land else ("excellent" if idx % 2 == 0 else "good"),
                    "district": loc.district,
                    "official_address": loc.official_address,
                    "unofficial_addresses": unofficial,
                    "location": loc,
                    "price": tmpl["price"],
                    "area_m2": tmpl["area_m2"],
                    "room_count": 1 if is_land else tmpl["room_count"],
                    "floor": None if is_land else tmpl.get("floor"),
                    "total_floor": None if is_land else tmpl.get("total_floor"),
                    "has_elevator": False if is_land else tmpl.get(
                        "has_elevator",
                        (tmpl.get("total_floor") or 0) >= 5,
                    ),
                    "window_count": None if is_land else tmpl.get(
                        "window_count",
                        tmpl.get("room_count", 2) + 1 if tmpl.get("property_type") == "apartment" else None,
                    ),
                    "bathroom_count": None if is_land else tmpl.get(
                        "bathroom_count",
                        max(1, tmpl.get("room_count", 2) - 1)
                        if tmpl.get("property_type") == "apartment"
                        else None,
                    ),
                    "view_direction": "" if is_land else tmpl.get(
                        "view_direction",
                        ["south", "east", "north", "west"][idx % 4]
                        if tmpl.get("property_type") == "apartment"
                        else "",
                    ),
                    "garage": False if is_land else tmpl.get("garage", False),
                    "balcony": False if is_land else tmpl.get("balcony", False),
                    "furnished": False if is_land else tmpl.get("furnished", False),
                    "payment_terms": [] if is_land else tmpl.get(
                        "payment_terms",
                        PAYMENT_TERM_POOLS[idx % len(PAYMENT_TERM_POOLS)],
                    ),
                    "year_built": None if is_land else 2018 + (idx % 5),
                    "parcel_number": tmpl.get("parcel_number", ""),
                    "land_right_type": tmpl.get("land_right_type", ""),
                    "land_use_type": tmpl.get("land_use_type", ""),
                    "land_contract_start": tmpl.get("land_contract_start"),
                    "land_contract_end": tmpl.get("land_contract_end"),
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "is_verified": tmpl.get("is_verified", False),
                    "is_vip": tmpl.get("is_vip", False),
                    "views_count": 50 + idx * 17,
                    "status": "active",
                    "images": images,
                    "is_active": True,
                    "listing_owner_type": owner_type,
                    "agent": agent_ref,
                    "posted_by": posted,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Demo users (password: demo1234):")
        self.stdout.write("  demo_admin          — Системийн үндсэн админ (платформ)")
        self.stdout.write("  demo_company_admin  — Company admin (RE/MAX HUB)")
        self.stdout.write("  demo_agent          — Агент (Ankhbileg.D, RE/MAX HUB)")
        self.stdout.write("  demo_owner          — Хувь хүн эзэн")
        self.stdout.write(f"Properties: {Property.objects.filter(is_active=True).count()}")
