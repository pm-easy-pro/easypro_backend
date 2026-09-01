import os
import re
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Agent, InviteCode, PhoneOTP
from .serializers import MeSerializer, ProfileUpdateSerializer
from .sms import SmsSendError, send_sms

User = get_user_model()

PHONE_RE = re.compile(r"^\d{8}$")
OTP_LENGTH = 6
OTP_TTL_SECONDS = 300
OTP_RESEND_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    # Strip Mongolia country code if pasted as 976XXXXXXXX
    if len(digits) == 11 and digits.startswith("976"):
        digits = digits[3:]
    return digits


def tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class OTPSendView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest = (
            PhoneOTP.objects.filter(phone=phone, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if latest and not latest.is_expired():
            elapsed = (timezone.now() - latest.created_at).total_seconds()
            if elapsed < OTP_RESEND_SECONDS:
                wait = int(OTP_RESEND_SECONDS - elapsed)
                return Response(
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
            expires_at=timezone.now() + timedelta(seconds=OTP_TTL_SECONDS),
        )

        sms_text = f"EasyPro баталгаажуулах код: {code}. {OTP_TTL_SECONDS // 60} минутын дотор оруулна уу."
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
                return Response(
                    {"detail": sms_error or "SMS илгээхэд алдаа гарлаа."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        payload = {
            "message": "Баталгаажуулах код илгээлээ." if sms_sent else "DEBUG: код үүсгэлээ (SMS илгээгдсэнгүй).",
            "phone": phone,
            "expires_in": OTP_TTL_SECONDS,
            "sms_sent": sms_sent,
        }
        if debug_otp:
            payload["debug_code"] = code
            if sms_error:
                payload["sms_error"] = sms_error

        return Response(payload, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        code = (request.data.get("code") or "").strip()

        if not PHONE_RE.match(phone):
            return Response(
                {"phone": "Утасны дугаар 8 оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code or not code.isdigit() or len(code) != OTP_LENGTH:
            return Response(
                {"code": f"Баталгаажуулах код {OTP_LENGTH} оронтой тоо байх ёстой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = (
            PhoneOTP.objects.filter(phone=phone, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not otp:
            return Response(
                {"detail": "Баталгаажуулах код олдсонгүй. Дахин илгээнэ үү."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if otp.is_expired():
            return Response(
                {"detail": "Кодын хугацаа дууссан. Дахин илгээнэ үү."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if otp.attempts >= OTP_MAX_ATTEMPTS:
            return Response(
                {"detail": "Оролдлогын хязгаар хэтэрсэн. Дахин код илгээнэ үү."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.code != code:
            PhoneOTP.objects.filter(pk=otp.pk).update(attempts=F("attempts") + 1)
            remaining = OTP_MAX_ATTEMPTS - (otp.attempts + 1)
            return Response(
                {
                    "detail": "Код буруу байна.",
                    "attempts_remaining": max(remaining, 0),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        is_new = False
        with transaction.atomic():
            user = User.objects.filter(username=phone).first()
            if not user:
                user = User(username=phone, phone=phone, profile_completed=False)
                user.set_unusable_password()
                user.save()
                is_new = True
            else:
                updates = []
                if user.phone != phone:
                    user.phone = phone
                    updates.append("phone")
                if updates:
                    user.save(update_fields=updates)

        tokens = tokens_for_user(user)
        me = MeSerializer(
            User.objects.select_related("agent_profile__organization").get(pk=user.pk)
        ).data

        return Response(
            {
                **tokens,
                "is_new": is_new,
                "profile_completed": user.profile_completed,
                "user": me,
            },
            status=status.HTTP_200_OK,
        )
