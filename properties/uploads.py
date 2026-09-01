import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_FILES_PER_REQUEST = 12


def public_media_url(stored_path: str, *, request=None) -> str:
    """Return a browser-ready URL for a stored media key/path."""
    url = default_storage.url(stored_path)
    if url.startswith("http://") or url.startswith("https://"):
        return url
    # Local filesystem fallback
    relative = url if url.startswith("/") else f"{settings.MEDIA_URL.rstrip('/')}/{url.lstrip('/')}"
    if request is not None:
        return request.build_absolute_uri(relative)
    return relative


def save_uploaded_images(files, *, request=None, folder: str = "properties/gallery") -> list[str]:
    if not files:
        raise ValueError("Зураг сонгоно уу.")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise ValueError(f"Нэг удаад хамгийн ихдээ {MAX_FILES_PER_REQUEST} зураг оруулна.")

    urls: list[str] = []
    day = timezone.now().strftime("%Y/%m/%d")

    for uploaded in files:
        content_type = (getattr(uploaded, "content_type", "") or "").lower()
        name = getattr(uploaded, "name", "image") or "image"
        ext = Path(name).suffix.lower()

        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(f"Зөвшөөрөгдөөгүй файл: {name}")
        elif not content_type and ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Зөвшөөрөгдөөгүй файл: {name}")

        size = getattr(uploaded, "size", 0) or 0
        if size > MAX_IMAGE_BYTES:
            raise ValueError(f"Зураг хэт том байна (хамгийн ихдээ 8MB): {name}")

        if ext not in ALLOWED_EXTENSIONS:
            ext = ".jpg"

        filename = f"{uuid.uuid4().hex}{ext}"
        key = f"{folder.strip('/')}/{day}/{filename}"
        stored_path = default_storage.save(key, uploaded)
        urls.append(public_media_url(stored_path, request=request))

    return urls
