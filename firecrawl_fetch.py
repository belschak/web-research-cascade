#!/usr/bin/env python3
"""
firecrawl_fetch.py -- Scrape ONE url to Markdown via the Firecrawl API.

Use sparingly. This is the last public fallback stage of the web-research
cascade, only when WebFetch AND Jina both fail on this URL. Firecrawl free
tier: ~1000 credits/month, 1 credit per scrape. Scrape only, never search.

(Search stays your built-in web search; this script only ever scrapes.)

STDLIB ONLY (urllib/json/sys/os) -- no pip installs. Cross-platform.

Setup: copy .env.example to .env and paste your key (see .env.example).

Usage:
    python firecrawl_fetch.py "https://example.com"
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Windows consoles default to cp1252 and choke on non-ASCII; force UTF-8 stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")
API_URL = "https://api.firecrawl.dev/v2/scrape"
TIMEOUT = 60  # scrape can render JS; give it room.


def _err(msg: str) -> None:
    """Print to stderr, never touch stdout (stdout is reserved for markdown)."""
    print(msg, file=sys.stderr)


def read_api_key() -> str:
    """
    Read FIRECRAWL_API_KEY from .env robustly: skip blank and '#'-comment
    lines, tolerate a UTF-8 BOM, accept the first line that starts with
    'FIRECRAWL_API_KEY=', trim surrounding quotes/whitespace, never log it.
    """
    if not os.path.exists(ENV_PATH):
        raise SystemExit(
            f"FIRECRAWL_API_KEY missing: no .env found at {ENV_PATH}. "
            f"Copy .env.example to .env and paste your key."
        )

    with open(ENV_PATH, "r", encoding="utf-8-sig") as f:  # utf-8-sig eats the BOM
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("FIRECRAWL_API_KEY="):
                value = line[len("FIRECRAWL_API_KEY="):].strip().strip('"').strip("'").strip()
                if value:
                    return value

    raise SystemExit("FIRECRAWL_API_KEY missing in .env")


def scrape(url: str, api_key: str) -> str:
    body = json.dumps({"url": url, "formats": [{"type": "markdown"}]}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        # nosec B310: request goes to the hardcoded https API_URL constant only.
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        code = e.code
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        hints = {
            401: "401 Unauthorized -- API key invalid or expired.",
            403: "403 Forbidden -- key has no access to this endpoint.",
            402: "402 Payment Required -- Firecrawl credits used up (~1000/month).",
            429: "429 Too Many Requests -- rate limit reached, retry later.",
        }
        raise SystemExit(f"Firecrawl {hints.get(code, f'HTTP {code}')} {detail}".rstrip())
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise SystemExit(f"Firecrawl request failed (network/timeout): {reason}")

    if not isinstance(payload, dict) or not payload.get("success", True):
        raise SystemExit(f"Firecrawl response not successful: {json.dumps(payload)[:300]}")

    data = payload.get("data") or {}
    markdown = data.get("markdown")
    if not markdown:
        raise SystemExit(
            f"Firecrawl returned no markdown (data.markdown empty). "
            f"Response keys: {list(data.keys())}"
        )
    return markdown


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python firecrawl_fetch.py "<url>"')
    url = sys.argv[1].strip()
    if not url or not url.lower().startswith(("http://", "https://")):
        raise SystemExit(f"Invalid URL (must start with http:// or https://): {url!r}")

    api_key = read_api_key()
    print(scrape(url, api_key))


if __name__ == "__main__":
    main()
