import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


class SmsSendError(Exception):
    """Raised when the SMS provider rejects the request."""


def send_sms(to: str, text: str) -> dict[str, Any]:
    """
    Send SMS via CallPro Text API.
    `to` must be an 8-digit Mongolian mobile number.
    """
    api_url = os.getenv("CALLPRO_SMS_API_URL", "https://api-text.callpro.mn/v1/sms/send")
    api_key = os.getenv("CALLPRO_SMS_API_KEY", "")
    sender = os.getenv("CALLPRO_SMS_FROM", "72727040")

    if not api_key:
        raise SmsSendError("CALLPRO_SMS_API_KEY тохируулаагүй байна.")

    payload = {
        "from": sender,
        "to": to,
        "text": text,
    }
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=20)
    except requests.RequestException as exc:
        logger.error("CallPro SMS network error: %s", exc)
        raise SmsSendError("SMS үйлчилгээнд холбогдож чадсангүй.") from exc

    if response.status_code >= 400:
        logger.error("CallPro SMS HTTP %s: %s", response.status_code, response.text)
        raise SmsSendError(f"SMS илгээхэд алдаа гарлаа ({response.status_code}).")

    try:
        return response.json() if response.text else {"ok": True}
    except ValueError:
        return {"ok": True, "raw": response.text}
