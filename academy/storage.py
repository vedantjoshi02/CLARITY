from io import BytesIO
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabasePrivateStorage(Storage):
    """
    Django storage backend for a private Supabase Storage bucket.

    Files are accessed only by the Django server. Do not expose the
    Supabase secret/service-role key to browser-side code.
    """

    timeout = 60

    def __init__(self):
        self.base_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
        self.api_key = getattr(settings, "SUPABASE_SECRET_KEY", "")
        self.bucket = getattr(
            settings, "SUPABASE_STORAGE_BUCKET", "clarity-documents"
        )

        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "Set SUPABASE_URL and SUPABASE_SECRET_KEY in the environment."
            )

        self.storage_url = f"{self.base_url}/storage/v1"

    def _headers(self, content_type=None):
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _object_url(self, name):
        # Preserve folder separators but safely encode each path component.
        safe_name = quote(name.lstrip("/"), safe="/")
        return f"{self.storage_url}/object/{quote(self.bucket, safe='')}/{safe_name}"

    def _open(self, name, mode="rb"):
        if mode not in ("rb", "r"):
            raise ValueError("Supabase storage supports read-only file access.")

        response = requests.get(
            self._object_url(name),
            headers=self._headers(),
            timeout=self.timeout,
        )
        if response.status_code in (400, 404):
            raise FileNotFoundError(name)
        response.raise_for_status()
        return File(BytesIO(response.content), name=name)

    def _save(self, name, content):
        content_type = getattr(content, "content_type", None) or "application/octet-stream"

        if hasattr(content, "chunks"):
            body = b"".join(content.chunks())
        else:
            body = content.read()

        response = requests.post(
            self._object_url(name),
            headers={
                **self._headers(content_type),
                "x-upsert": "true",
                "Cache-Control": "max-age=3600",
            },
            data=body,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return name

    def exists(self, name):
        response = requests.head(
            self._object_url(name),
            headers=self._headers(),
            timeout=self.timeout,
        )

        if response.status_code in (400, 404):
            return False

        response.raise_for_status()
        return True

    def delete(self, name):
        response = requests.delete(
            f"{self.storage_url}/object/{quote(self.bucket, safe='')}",
            headers=self._headers("application/json"),
            json={"prefixes": [name.lstrip("/")]},
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return
        response.raise_for_status()

    def size(self, name):
        response = requests.head(
            self._object_url(name),
            headers=self._headers(),
            timeout=self.timeout,
        )
        if response.status_code in (400, 404):
            raise FileNotFoundError(name)
        response.raise_for_status()
        value = response.headers.get("Content-Length")
        if value is None:
            raise NotImplementedError("Supabase did not return Content-Length.")
        return int(value)

    def url(self, name):
        # Generate a short-lived URL; the bucket itself remains private.
        response = requests.post(
            f"{self.storage_url}/object/sign/"
            f"{quote(self.bucket, safe='')}/{quote(name.lstrip('/'), safe='/')}",
            headers=self._headers("application/json"),
            json={"expiresIn": 60},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        signed_path = payload.get("signedURL") or payload.get("signedUrl")
        if not signed_path:
            raise RuntimeError("Supabase did not return a signed URL.")
        if signed_path.startswith(("http://", "https://")):
            return signed_path
        if not signed_path.startswith("/"):
            signed_path = "/" + signed_path
        # Supabase usually returns a path relative to /storage/v1,
        # but handle the case where it already includes that prefix.
        if signed_path.startswith("/storage/v1"):
            return f"{self.base_url}{signed_path}"
        return f"{self.storage_url}{signed_path}"