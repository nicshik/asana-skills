"""Shared Asana REST API client utilities.

These helpers talk to the Asana REST API (``https://app.asana.com/api/1.0``)
with a Personal Access Token. The token is read from the environment or a local
env file, is never printed, and is redacted from error output. A hard request
timeout keeps calls from hanging.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASE = "https://app.asana.com/api/1.0"
ENV_KEY = "ASANA_ACCESS_TOKEN"
DEFAULT_TIMEOUT = 30


class AsanaApiError(Exception):
    def __init__(self, category: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.details = details or {}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return values

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def candidate_env_files(env_file: str | None = None, cwd: Path | None = None) -> list[Path]:
    paths: list[Path] = []
    if env_file:
        paths.append(Path(env_file).expanduser())
    if os.environ.get("ASANA_ENV_FILE"):
        paths.append(Path(os.environ["ASANA_ENV_FILE"]).expanduser())

    search_root = cwd or Path.cwd()
    for base in [search_root, *search_root.parents]:
        paths.extend([base / ".env.local", base / ".env"])

    paths.append(search_root / "app" / ".env.local")

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve() if path.exists() else path
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def resolve_token(env_file: str | None = None) -> str:
    token = os.environ.get(ENV_KEY)
    if token:
        return token

    for path in candidate_env_files(env_file):
        token = parse_env_file(path).get(ENV_KEY)
        if token:
            return token

    raise AsanaApiError(
        "missing_token",
        f"{ENV_KEY} was not found in the environment, ASANA_ENV_FILE, --env-file, "
        "or local .env files.",
    )


def build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore[import-not-found]

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def sanitize_text(value: str, token: str | None = None) -> str:
    sanitized = value
    if token:
        sanitized = sanitized.replace(token, "[redacted]")
    return sanitized


class AsanaClient:
    def __init__(self, token: str, api_base: str = API_BASE, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.api_base = api_base
        self.token = token
        self.timeout = timeout
        self.ctx = build_ssl_context()

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        wrap: bool = True,
        full: bool = False,
    ) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        url = self.api_base + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        body = None
        if data is not None:
            body = json.dumps({"data": data} if wrap else data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, context=self.ctx, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
                payload = json.loads(text) if text.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = sanitize_text(exc.read().decode("utf-8", errors="replace"), self.token)
            category = {
                401: "permission_denied",
                403: "permission_denied",
                402: "premium_required",
                404: "not_found",
                429: "rate_limited",
            }.get(exc.code, "http_error")
            raise AsanaApiError(category, f"Asana API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = sanitize_text(str(exc.reason), self.token)
            raise AsanaApiError("network", f"Asana API request failed: {reason}") from exc
        except TimeoutError:
            raise AsanaApiError("timeout", f"Asana API request timed out after {self.timeout}s") from None

        if isinstance(payload, dict) and payload.get("errors"):
            errors = sanitize_text(json.dumps(payload["errors"], ensure_ascii=False, indent=2), self.token)
            raise AsanaApiError("api_error", errors)

        if full:
            return payload
        return payload.get("data") if isinstance(payload, dict) else payload

    def get_all(self, path: str, params: dict[str, Any] | None = None, page_size: int = 100) -> list[Any]:
        """Follow ``next_page`` for collection endpoints and return all rows."""
        out: list[Any] = []
        params = dict(params or {})
        params.setdefault("limit", page_size)
        offset: str | None = None
        while True:
            page = dict(params)
            if offset:
                page["offset"] = offset
            payload = self.request("GET", path, params=page, full=True)
            out.extend(payload.get("data") or [])
            offset = (payload.get("next_page") or {}).get("offset")
            if not offset:
                break
        return out
