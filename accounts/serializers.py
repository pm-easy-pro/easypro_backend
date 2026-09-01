from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Agent, InviteCode

User = get_user_model()


def absolute_media_url(request, file_field):
    if not file_field:
        return None
    url = file_field.url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return request.build_absolute_uri(url) if request else url


class OrganizationBriefSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(source="get_display_label", read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            "id",
            "company_name",
            "display_label",
            "phone",
            "email",
            "address",
            "bio",
            "slug",
            "is_verified",
            "avatar_url",
        ]

    def get_avatar_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.avatar)


class AgentSummarySerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(source="get_display_label", read_only=True)
    organization_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    membership_status_display = serializers.CharField(
        source="get_membership_status_display", read_only=True
    )

    class Meta:
        model = Agent
        fields = [
            "id",
            "agent_type",
            "display_name",
            "company_name",
            "title",
            "display_label",
            "organization_name",
            "phone",
            "email",
            "address",
            "slug",
            "is_verified",
            "membership_status",
            "membership_status_display",
            "avatar_url",
            "created_at",
        ]

    def get_organization_name(self, obj):
        if obj.organization_id:
            return obj.organization.get_display_label()
        return None

    def get_avatar_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.avatar)


class MembershipRequestSerializer(AgentSummarySerializer):
    invite_code = serializers.CharField(source="invited_via.code", read_only=True, default=None)
    username = serializers.CharField(source="user.username", read_only=True, default=None)
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True, default=None
    )

    class Meta(AgentSummarySerializer.Meta):
        fields = AgentSummarySerializer.Meta.fields + [
            "invite_code",
            "username",
            "reviewed_at",
            "reviewed_by_username",
        ]


class PropertyAgentSerializer(AgentSummarySerializer):
    """Rich agent payload for property detail sidebar."""

    bio = serializers.CharField(read_only=True)
    organization_detail = OrganizationBriefSerializer(source="organization", read_only=True)

    class Meta(AgentSummarySerializer.Meta):
        fields = AgentSummarySerializer.Meta.fields + [
            "bio",
            "organization_detail",
        ]


class AgentDetailSerializer(AgentSummarySerializer):
    member_agents = serializers.SerializerMethodField()
    property_count = serializers.SerializerMethodField()
    organization_detail = OrganizationBriefSerializer(source="organization", read_only=True)
    bio = serializers.CharField(read_only=True)

    class Meta(AgentSummarySerializer.Meta):
        fields = list(
            dict.fromkeys(
                AgentSummarySerializer.Meta.fields
                + [
                    "bio",
                    "organization_detail",
                    "member_agents",
                    "property_count",
                ]
            )
        )

    def get_member_agents(self, obj):
        members = obj.member_agents.filter(
            is_active=True,
            membership_status=Agent.MEMBERSHIP_APPROVED,
        ).select_related("organization")
        return AgentSummarySerializer(members, many=True, context=self.context).data

    def get_property_count(self, obj):
        return obj.properties.filter(is_active=True, status="active").count()


class CompanyAdminBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone"]


class AgentCompanyManageSerializer(serializers.ModelSerializer):
    """Staff CRUD payload for agent companies / organizations."""

    display_label = serializers.CharField(source="get_display_label", read_only=True)
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    clear_avatar = serializers.BooleanField(required=False, write_only=True, default=False)
    member_count = serializers.SerializerMethodField()
    property_count = serializers.SerializerMethodField()
    admin = CompanyAdminBriefSerializer(source="user", read_only=True)

    admin_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admin_password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)
    admin_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    admin_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "company_name",
            "display_label",
            "slug",
            "phone",
            "email",
            "address",
            "bio",
            "is_verified",
            "is_active",
            "avatar",
            "avatar_url",
            "clear_avatar",
            "member_count",
            "property_count",
            "admin",
            "admin_username",
            "admin_password",
            "admin_email",
            "admin_phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "company_name": {"required": True, "allow_blank": False},
            "slug": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
            "bio": {"required": False, "allow_blank": True},
        }

    def get_avatar_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.avatar)

    def get_member_count(self, obj):
        return obj.member_agents.filter(
            is_active=True,
            membership_status=Agent.MEMBERSHIP_APPROVED,
        ).count()

    def get_property_count(self, obj):
        return obj.properties.filter(is_active=True, status="active").count()

    def validate_company_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Компанийн нэр оруулна уу.")
        return value

    def validate(self, attrs):
        creating = self.instance is None
        username = (attrs.get("admin_username") or "").strip()
        password = attrs.get("admin_password") or ""

        if creating:
            if not username:
                raise serializers.ValidationError(
                    {"admin_username": "Company admin хэрэглэгчийн нэр оруулна уу."}
                )
            if not password:
                raise serializers.ValidationError(
                    {"admin_password": "Company admin нууц үг оруулна уу."}
                )
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError(
                    {"admin_username": "Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн."}
                )
        elif username or password or attrs.get("admin_email") is not None or attrs.get("admin_phone") is not None:
            if self.instance and self.instance.user_id:
                if username and username != self.instance.user.username:
                    if User.objects.filter(username=username).exclude(pk=self.instance.user_id).exists():
                        raise serializers.ValidationError(
                            {"admin_username": "Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн."}
                        )
            else:
                if not username:
                    raise serializers.ValidationError(
                        {"admin_username": "Company admin хэрэглэгчийн нэр оруулна уу."}
                    )
                if not password:
                    raise serializers.ValidationError(
                        {"admin_password": "Company admin нууц үг оруулна уу."}
                    )
                if User.objects.filter(username=username).exists():
                    raise serializers.ValidationError(
                        {"admin_username": "Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн."}
                    )

        attrs["admin_username"] = username
        return attrs

    def _create_admin_user(self, *, username, password, email, phone):
        return User.objects.create_user(
            username=username,
            email=email or "",
            password=password,
            phone=phone or "",
        )

    def _apply_admin(self, company, validated_data):
        username = validated_data.pop("admin_username", "")
        password = validated_data.pop("admin_password", "")
        email = validated_data.pop("admin_email", None)
        phone = validated_data.pop("admin_phone", None)

        if not username and not password and email is None and phone is None:
            return

        if company.user_id:
            admin = company.user
            if username:
                admin.username = username
            if email is not None:
                admin.email = email
            if phone is not None:
                admin.phone = phone
            if password:
                admin.set_password(password)
            admin.save()
        elif username and password:
            admin = self._create_admin_user(
                username=username,
                password=password,
                email=email or company.email,
                phone=phone if phone is not None else company.phone,
            )
            company.user = admin
            company.save(update_fields=["user", "updated_at"])

    def create(self, validated_data):
        from django.db import transaction

        validated_data.pop("clear_avatar", None)
        avatar = validated_data.pop("avatar", None)
        admin_username = validated_data.pop("admin_username")
        admin_password = validated_data.pop("admin_password")
        admin_email = validated_data.pop("admin_email", "") or ""
        admin_phone = validated_data.pop("admin_phone", "") or ""

        with transaction.atomic():
            admin = self._create_admin_user(
                username=admin_username,
                password=admin_password,
                email=admin_email or validated_data.get("email", ""),
                phone=admin_phone or validated_data.get("phone", ""),
            )
            company = Agent(
                agent_type=Agent.TYPE_ORGANIZATION,
                user=admin,
                **validated_data,
            )
            if avatar:
                company.avatar = avatar
            company.save()
        return company

    def update(self, instance, validated_data):
        clear_avatar = validated_data.pop("clear_avatar", False)
        avatar = validated_data.pop("avatar", None)

        admin_fields = {
            "admin_username": validated_data.pop("admin_username", ""),
            "admin_password": validated_data.pop("admin_password", ""),
            "admin_email": validated_data.pop("admin_email", None),
            "admin_phone": validated_data.pop("admin_phone", None),
        }

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if clear_avatar and not avatar:
            if instance.avatar:
                instance.avatar.delete(save=False)
            instance.avatar = None
        elif avatar is not None:
            instance.avatar = avatar

        instance.agent_type = Agent.TYPE_ORGANIZATION
        instance.save()
        self._apply_admin(instance, admin_fields)
        return instance


class InviteCodeSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.get_display_label", read_only=True)
    is_redeemable = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = InviteCode
        fields = [
            "id",
            "organization",
            "organization_name",
            "code",
            "max_uses",
            "uses_count",
            "expires_at",
            "note",
            "is_active",
            "is_redeemable",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "code",
            "uses_count",
            "created_by",
            "organization",
            "created_at",
            "updated_at",
        ]

    def get_is_redeemable(self, obj):
        return obj.is_redeemable()


class InviteCodeCreateSerializer(serializers.Serializer):
    max_uses = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.filter(agent_type=Agent.TYPE_ORGANIZATION, is_active=True),
        required=False,
    )


class InvitePreviewSerializer(serializers.Serializer):
    code = serializers.CharField()
    organization_id = serializers.IntegerField()
    organization_name = serializers.CharField()
    is_valid = serializers.BooleanField()
    message = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "display_name",
            "avatar_url",
        ]

    def get_display_name(self, obj):
        full = obj.get_full_name().strip()
        return full or obj.username

    def get_avatar_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.avatar)


class MeSerializer(serializers.ModelSerializer):
    agent_profile = AgentSummarySerializer(read_only=True)
    is_company_admin = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "display_name",
            "agent_profile",
            "is_staff",
            "is_company_admin",
            "profile_completed",
        ]

    def get_is_company_admin(self, obj):
        profile = getattr(obj, "agent_profile", None)
        return bool(
            profile
            and profile.agent_type == Agent.TYPE_ORGANIZATION
            and profile.is_active
        )

    def get_display_name(self, obj):
        profile = getattr(obj, "agent_profile", None)
        if profile and (profile.display_name or profile.company_name):
            return profile.display_name or profile.company_name
        full = obj.get_full_name().strip()
        return full or obj.username


class ProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    profile_type = serializers.ChoiceField(
        choices=["owner", "agent"],
        required=False,
    )
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    title = serializers.CharField(required=False, allow_blank=True, max_length=120)
    invite_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        profile_type = attrs.get("profile_type")
        raw_code = (attrs.get("invite_code") or "").strip().upper()

        if profile_type == "agent" or raw_code:
            if not raw_code:
                raise serializers.ValidationError(
                    {"invite_code": "Агент болгохын тулд компанийн урилгын код оруулна уу."}
                )
            invite = (
                InviteCode.objects.select_related("organization")
                .filter(code__iexact=raw_code)
                .first()
            )
            if not invite or not invite.is_redeemable():
                raise serializers.ValidationError(
                    {"invite_code": "Урилгын код хүчингүй эсвэл хугацаа дууссан."}
                )
            display_name = (attrs.get("display_name") or "").strip()
            if not display_name:
                raise serializers.ValidationError({"display_name": "Агентын нэр оруулна уу."})
            attrs["invite"] = invite
            attrs["profile_type"] = "agent"
            attrs["invite_code"] = raw_code
            attrs["display_name"] = display_name
        elif profile_type == "owner":
            first = (attrs.get("first_name") or "").strip()
            if not first:
                raise serializers.ValidationError({"first_name": "Нэрээ оруулна уу."})
            attrs["first_name"] = first

        return attrs

    def update(self, user, validated_data):
        from django.db import transaction
        from django.db.models import F

        invite = validated_data.pop("invite", None)
        validated_data.pop("invite_code", None)
        profile_type = validated_data.pop("profile_type", None)
        display_name = validated_data.pop("display_name", "")
        title = validated_data.pop("title", "")

        with transaction.atomic():
            if "first_name" in validated_data:
                user.first_name = validated_data.get("first_name") or user.first_name
            if "last_name" in validated_data:
                user.last_name = validated_data.get("last_name") or ""
            if "email" in validated_data:
                user.email = validated_data.get("email") or ""

            if invite:
                existing = getattr(user, "agent_profile", None)
                if existing and existing.agent_type == Agent.TYPE_INDIVIDUAL:
                    existing.organization = invite.organization
                    existing.display_name = display_name
                    existing.title = title or existing.title
                    existing.phone = user.phone or existing.phone
                    existing.email = user.email or existing.email
                    existing.membership_status = Agent.MEMBERSHIP_PENDING
                    existing.is_verified = False
                    existing.invited_via = invite
                    existing.save()
                elif not existing:
                    Agent.objects.create(
                        agent_type=Agent.TYPE_INDIVIDUAL,
                        user=user,
                        organization=invite.organization,
                        display_name=display_name,
                        title=title or "",
                        phone=user.phone or "",
                        email=user.email or "",
                        is_verified=False,
                        membership_status=Agent.MEMBERSHIP_PENDING,
                        invited_via=invite,
                    )
                else:
                    raise serializers.ValidationError(
                        {"profile_type": "Энэ хэрэглэгч агент профайл үүсгэх боломжгүй."}
                    )
                InviteCode.objects.filter(pk=invite.pk).update(uses_count=F("uses_count") + 1)
                if not user.first_name:
                    user.first_name = display_name

            if profile_type in ("owner", "agent") or invite:
                user.profile_completed = True

            user.save()

        return user


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    phone = serializers.CharField(required=False, allow_blank=True)
    agent_type = serializers.ChoiceField(
        choices=[Agent.TYPE_INDIVIDUAL],
        required=False,
    )
    display_name = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    invite_code = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн.")
        return value

    def validate(self, attrs):
        raw_code = (attrs.get("invite_code") or "").strip().upper()
        agent_type = attrs.get("agent_type")

        if raw_code:
            invite = (
                InviteCode.objects.select_related("organization")
                .filter(code__iexact=raw_code)
                .first()
            )
            if not invite or not invite.is_redeemable():
                raise serializers.ValidationError(
                    {"invite_code": "Урилгын код хүчингүй эсвэл хугацаа дууссан."}
                )
            attrs["invite"] = invite
            attrs["agent_type"] = Agent.TYPE_INDIVIDUAL
            if not (attrs.get("display_name") or "").strip():
                raise serializers.ValidationError(
                    {"display_name": "Агентын нэр оруулна уу."}
                )
        elif agent_type == Agent.TYPE_INDIVIDUAL:
            raise serializers.ValidationError(
                {
                    "invite_code": "Агент бүртгүүлэхийн тулд компанийн урилгын код оруулна уу."
                }
            )
        elif agent_type:
            raise serializers.ValidationError(
                {"agent_type": "Компани зөвхөн платформ админ бүртгэнэ."}
            )

        attrs["invite_code"] = raw_code
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from django.db.models import F

        invite = validated_data.pop("invite", None)
        validated_data.pop("invite_code", None)
        agent_type = validated_data.pop("agent_type", None)
        display_name = validated_data.pop("display_name", "")
        title = validated_data.pop("title", "")
        phone = validated_data.pop("phone", "")

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data.get("email", ""),
                password=validated_data["password"],
                phone=phone,
            )

            if invite:
                Agent.objects.create(
                    agent_type=Agent.TYPE_INDIVIDUAL,
                    user=user,
                    organization=invite.organization,
                    display_name=display_name or user.username,
                    title=title or "",
                    phone=phone,
                    email=user.email,
                    is_verified=False,
                    membership_status=Agent.MEMBERSHIP_PENDING,
                    invited_via=invite,
                )
                InviteCode.objects.filter(pk=invite.pk).update(uses_count=F("uses_count") + 1)
            elif agent_type:
                Agent.objects.create(
                    agent_type=agent_type,
                    user=user,
                    display_name=display_name or user.get_full_name() or user.username,
                    phone=phone,
                    email=user.email,
                    membership_status=Agent.MEMBERSHIP_APPROVED,
                )

        return user
