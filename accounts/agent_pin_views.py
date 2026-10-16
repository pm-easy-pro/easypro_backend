import os
import re
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agent, PhoneOTP
from .otp_views import (
    OTP_LENGTH,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_SECONDS,
    OTP_TTL_SECONDS,
    PHONE_RE,
    normalize_phone,
    tokens_for_user,
)
from .serializers import MeSerializer
from .sms import SmsSendError, send_sms

User = get_user_model()

PIN_RE = re.compile(r"^\d{6}$")
PIN_MAX_ATTEMPTS = 5
PIN_LOCK_MINUTES = 15


def find_approved_individual_agent(phone: str):
    """Return (user, agent) for an approved individual agent matching phone."""
    user = (
        User.objects.filter(phone=phone)
        .select_related("agent_profile__organization")
        .first()
    )
    if not user:
        # Also try username=phone (OTP consumers)
        user = (
            User.objects.filter(username=phone)
            .select_related("agent_profile__organization")
            .first()
        )
    if not user:
        return None, None
    profile = getattr(user, "agent_profile", None)
    if (
        not profile
        or profile.agent_type != Agent.TYPE_INDIVIDUAL
        or not profile.is_active
        or profile.membership_status != Agent.MEMBERSHIP_APPROVED
    ):
        return None, None
    return user, profile


def send_purpose_otp(phone: str, purpose: str, sms_prefix: str):
    latest = (
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if latest and not latest.is_expired():
        elapsed = (timezone.now() - latest.created_at).total_seconds()
        if elapsed < OTP_RESEND_SECONDS:
            wait = int(OTP_RESEND_SECONDS - elapsed)
            return None, Response(
                {
                    "detail": f"Дахин код авахын тулд {wait} секунд хүлээнэ үү.",
                    "retry_after": wait,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    code = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))
    otp = PhoneOTP.objects.create(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=OTP_TTL_SECONDS),
    )
    sms_text = (
        f"{sms_prefix}: {code}. {OTP_TTL_SECONDS // 60} минутын дотор оруулна уу."
    )
    debug_otp = os.getenv("OTP_DEBUG", "false").lower() in ("true", "1", "yes")
    sms_sent = False
    sms_error = None
    try:
        send_sms(phone, sms_text)
        sms_sent = True
    except SmsSendError as exc:
        sms_error = str(exc)
        if not debug_otp:
            otp.delete()
            return None, Response(
                {"detail": sms_error or "SMS илгээхэд алдаа гарлаа."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    payload = {
        "message": "Баталгаажуулах код илгээлээ." if sms_sent else "DEBUG: код үүсгэлээ.",
        "phone": phone,
        "expires_in": OTP_TTL_SECONDS,
        "sms_sent": sms_sent,
    }
    if debug_otp:
        payload["debug_code"] = code
        if sms_error:
            payload["sms_error"] = sms_error
    return otp, Response(payload, status=status.HTTP_200_OK)


def verify_purpose_otp(phone: str, code: str, purpose: str):
    otp = (
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp:
        return None, Response(
            {"detail": "Баталгаажуулах код олдсонгүй. Дахин илгээнэ үү."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if otp.is_expired():
        return None, Response(
            {"detail": "Кодын хугацаа дууссан. Дахин илгээнэ үү."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        return None, Response(
            {"detail": "Оролдлогын хязгаар хэтэрсэн. Дахин код илгээнэ үү."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if otp.code != code:
        PhoneOTP.objects.filter(pk=otp.pk).update(attempts=F("attempts") + 1)
        remaining = OTP_MAX_ATTEMPTS - (otp.attempts + 1)
        return None, Response(
            {
                "detail": "Код буруу байна.",
                "attempts_remaining": max(remaining, 0),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return otp, None


def validate_pin_pair(pin: str, pin_confirm: str | None = None):
    if not PIN_RE.match(pin or ""):
        return "PIN код 6 оронтой тоо байх ёстой."
    if pin_confirm is not None and pin != pin_confirm:
        return "PIN код таарахгүй байна."
    return None


def me_payload(user):
    me = MeSerializer(
        User.objects.select_related("agent_profile__organization").get(pk=user.pk)
    ).data
    tokens = tokens_for_user(user)
    return {**tokens, "user": me}


class AgentPinStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user, agent = find_approved_individual_agent(phone)
        if not user or not agent:
            return Response(
                {
                    "detail": "Энэ утастай баталгаажсан агент олдсонгүй.",
                    "is_agent": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        has_pin = user.has_agent_pin()
        return Response(
            {
                "phone": phone,
                "is_agent": True,
                "has_pin": has_pin,
                "needs_setup": not has_pin,
                "display_name": agent.get_display_label(),
            }
        )


class AgentPinSetupSendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user, _agent = find_approved_individual_agent(phone)
        if not user:
            return Response(
                {"detail": "Энэ утастай баталгаажсан агент олдсонгүй."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.has_agent_pin():
            return Response(
                {"detail": "PIN аль хэдийн тохируулагдсан. Нэвтрэх эсвэл reset хийнэ үү."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _otp, response = send_purpose_otp(
            phone,
            PhoneOTP.PURPOSE_AGENT_PIN_SETUP,
            "EasyPro Agent PIN тохиргоо",
        )
        return response


class AgentPinSetupVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        code = (request.data.get("code") or "").strip()
        pin = (request.data.get("pin") or "").strip()
        pin_confirm = (request.data.get("pin_confirm") or "").strip()

        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pin_err = validate_pin_pair(pin, pin_confirm)
        if pin_err:
            return Response({"detail": pin_err}, status=status.HTTP_400_BAD_REQUEST)

        user, _agent = find_approved_individual_agent(phone)
        if not user:
            return Response(
                {"detail": "Энэ утастай баталгаажсан агент олдсонгүй."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.has_agent_pin():
            return Response(
                {"detail": "PIN аль хэдийн тохируулагдсан."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        _otp, err = verify_purpose_otp(phone, code, PhoneOTP.PURPOSE_AGENT_PIN_SETUP)
        if err:
            return err

        user.set_agent_pin(pin)
        if user.phone != phone:
            user.phone = phone
        user.save(
            update_fields=[
                "agent_pin_hash",
                "agent_pin_set_at",
                "agent_pin_failed_attempts",
                "agent_pin_locked_until",
                "phone",
            ]
        )
        return Response(me_payload(user), status=status.HTTP_200_OK)


class AgentPinLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        pin = (request.data.get("pin") or "").strip()

        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not PIN_RE.match(pin):
            return Response(
                {"detail": "PIN код 6 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, _agent = find_approved_individual_agent(phone)
        if not user or not user.has_agent_pin():
            return Response(
                {"detail": "Нэвтрэх мэдээлэл буруу байна."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.agent_pin_locked_until and user.agent_pin_locked_until > timezone.now():
            mins = max(
                1,
                int(
                    (user.agent_pin_locked_until - timezone.now()).total_seconds() / 60
                ),
            )
            return Response(
                {"detail": f"Хэт олон буруу оролдлого. {mins} минутын дараа дахин оролдоно уу."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not user.check_agent_pin(pin):
            user.agent_pin_failed_attempts = (user.agent_pin_failed_attempts or 0) + 1
            updates = ["agent_pin_failed_attempts"]
            if user.agent_pin_failed_attempts >= PIN_MAX_ATTEMPTS:
                user.agent_pin_locked_until = timezone.now() + timedelta(
                    minutes=PIN_LOCK_MINUTES
                )
                user.agent_pin_failed_attempts = 0
                updates.append("agent_pin_locked_until")
            user.save(update_fields=updates)
            return Response(
                {"detail": "Нэвтрэх мэдээлэл буруу байна."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.agent_pin_failed_attempts = 0
        user.agent_pin_locked_until = None
        user.save(update_fields=["agent_pin_failed_attempts", "agent_pin_locked_until"])
        return Response(me_payload(user), status=status.HTTP_200_OK)


class AgentPinResetSendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user, _agent = find_approved_individual_agent(phone)
        if not user:
            return Response(
                {"detail": "Энэ утастай баталгаажсан агент олдсонгүй."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not user.has_agent_pin():
            return Response(
                {"detail": "PIN тохируулаагүй. Эхлээд setup хийнэ үү."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _otp, response = send_purpose_otp(
            phone,
            PhoneOTP.PURPOSE_AGENT_PIN_RESET,
            "EasyPro Agent PIN reset",
        )
        return response


class AgentPinResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        code = (request.data.get("code") or "").strip()
        pin = (request.data.get("pin") or "").strip()
        pin_confirm = (request.data.get("pin_confirm") or "").strip()

        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pin_err = validate_pin_pair(pin, pin_confirm)
        if pin_err:
            return Response({"detail": pin_err}, status=status.HTTP_400_BAD_REQUEST)

        user, _agent = find_approved_individual_agent(phone)
        if not user:
            return Response(
                {"detail": "Энэ утастай баталгаажсан агент олдсонгүй."},
                status=status.HTTP_404_NOT_FOUND,
            )

        _otp, err = verify_purpose_otp(phone, code, PhoneOTP.PURPOSE_AGENT_PIN_RESET)
        if err:
            return err

        user.set_agent_pin(pin)
        user.save(
            update_fields=[
                "agent_pin_hash",
                "agent_pin_set_at",
                "agent_pin_failed_attempts",
                "agent_pin_locked_until",
            ]
        )
        return Response(me_payload(user), status=status.HTTP_200_OK)


class AgentPinStaffSetView(APIView):
    """Staff / company admin: set or reset an individual agent's PIN without SMS."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .permissions import can_manage_agents, scoped_agents_queryset

        if not can_manage_agents(request.user):
            return Response(
                {"detail": "Зөвшөөрөлгүй."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pin = (request.data.get("pin") or "").strip()
        pin_confirm = (request.data.get("pin_confirm") or "").strip()
        pin_err = validate_pin_pair(pin, pin_confirm)
        if pin_err:
            return Response({"detail": pin_err}, status=status.HTTP_400_BAD_REQUEST)

        agent = (
            scoped_agents_queryset(request.user)
            .filter(pk=pk, agent_type=Agent.TYPE_INDIVIDUAL)
            .select_related("user")
            .first()
        )
        if not agent or not agent.user_id:
            return Response(
                {"detail": "Агент олдсонгүй."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = agent.user
        was_set = user.has_agent_pin()
        user.set_agent_pin(pin)
        if agent.phone and user.phone != agent.phone:
            user.phone = normalize_phone(agent.phone) or user.phone
        user.save(
            update_fields=[
                "agent_pin_hash",
                "agent_pin_set_at",
                "agent_pin_failed_attempts",
                "agent_pin_locked_until",
                "phone",
            ]
        )
        return Response(
            {
                "detail": "PIN шинэчлэгдлээ." if was_set else "PIN тохируулагдлаа.",
                "agent_id": agent.id,
                "has_pin": True,
                "pin_set_at": user.agent_pin_set_at,
            },
            status=status.HTTP_200_OK,
        )
