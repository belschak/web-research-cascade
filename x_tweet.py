#!/usr/bin/env python3
"""
x_tweet.py -- Fetch a single public tweet as Markdown via X's no-auth
syndication endpoint (the same route x.com uses to render embeds).

Why this exists: Jina and Firecrawl are blocked wholesale by x.com/twitter.com
(they demand a logged-in session and reject datacenter IPs). For a SINGLE public
tweet, the syndication route needs no auth and no key. For threads/profiles/search
there is no free API route -- use the browser MCP with your login (skill stage 4).

STDLIB ONLY (urllib) -- no pip installs. Cross-platform (uses no OS-specific paths).

Usage:
    python x_tweet.py "https://x.com/jack/status/20"
    python x_tweet.py 20                 # bare tweet id also accepted
    python x_tweet.py "https://twitter.com/BarackObama/status/266031293945503744"

The endpoint is unofficial and can tighten without notice; on failure the skill
falls back to the browser MCP with login.
"""
from __future__ import annotations

import json
import math
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Windows consoles default to cp1252 and choke on emoji; force UTF-8 stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# A browser-like UA; the endpoint rejects some generic/script UAs.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
BASE = "https://cdn.syndication.twimg.com/tweet-result"


def extract_id(arg: str) -> str | None:
    """Pull the numeric tweet id from a URL or accept a bare id."""
    arg = arg.strip()
    if arg.isdigit():
        return arg
    m = re.search(r"(?:x\.com|twitter\.com)/[^/]+/status(?:es)?/(\d+)", arg)
    if m:
        return m.group(1)
    m = re.search(r"(\d{5,25})", arg)  # last resort: a long number in the string
    return m.group(1) if m else None


def js_base36_token(tweet_id: str) -> str:
    """
    Replicate the twitter embed JS token:
        ((id / 1e15) * Math.PI).toString(36).replace(/(0+|\\.)/g, '')
    Only used as a fallback if token='a' is ever rejected. token='a' currently
    works for all tweets; this is future-proofing.
    """
    n = (int(tweet_id) / 1e15) * math.pi
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    int_part = int(n)
    frac = n - int_part
    out = ""
    if int_part == 0:
        out = "0"
    else:
        ip = int_part
        while ip > 0:
            out = digits[ip % 36] + out
            ip //= 36
    if frac > 0:
        out += "."
        for _ in range(20):
            frac *= 36
            d = int(frac)
            out += digits[d]
            frac -= d
            if frac == 0:
                break
    return re.sub(r"(0+|\.)", "", out)


def _get_json(tweet_id: str, token: str):
    url = f"{BASE}?id={tweet_id}&token={token}&lang=en"
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    # nosec B310: BASE is a hardcoded https constant; id and token are derived values.
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def fetch_tweet(tweet_id: str) -> dict:
    """Try token='a' (works today), fall back to the computed token on 404/non-JSON."""
    last_err = None
    # token='a' works today; the computed token is only built if that fails.
    for make_token in (lambda: "a", lambda: js_base36_token(tweet_id)):
        token = make_token()
        try:
            return _get_json(tweet_id, token)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code not in (404, 403):
                raise
        except json.JSONDecodeError as e:
            last_err = e
    # Both attempts failed.
    if isinstance(last_err, urllib.error.HTTPError) and last_err.code == 404:
        raise SystemExit(
            f"Tweet {tweet_id}: 404. Likely deleted, protected/private, or the "
            f"syndication route was tightened. Fallback: open it via the browser MCP "
            f"with your login (web-research-cascade skill, stage 4)."
        )
    raise SystemExit(f"Tweet {tweet_id}: could not fetch ({last_err!r}).")


# ---- rendering -------------------------------------------------------------

def _expand_text(data: dict) -> str:
    """Replace t.co short URLs with their expanded targets."""
    text = data.get("text") or data.get("full_text") or ""
    ents = data.get("entities") or {}
    for u in ents.get("urls", []) or []:
        short, expanded = u.get("url"), u.get("expanded_url")
        if short and expanded:
            text = text.replace(short, expanded)
    # Drop the trailing t.co media link (media is listed separately below).
    for m in ents.get("media", []) or []:
        if m.get("url"):
            text = text.replace(m["url"], "").rstrip()
    return text.strip()


def _fmt_ts(created_at: str | None) -> str:
    if not created_at:
        return "?"
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return created_at


def _media_lines(data: dict) -> list[str]:
    lines: list[str] = []
    for m in data.get("mediaDetails") or []:
        mtype = m.get("type")
        if mtype == "photo":
            lines.append(f"- Photo: {m.get('media_url_https')}")
        elif mtype in ("video", "animated_gif"):
            variants = ((m.get("video_info") or {}).get("variants")) or []
            mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
            best = max(mp4s, key=lambda v: v.get("bitrate", 0)) if mp4s else None
            url = best.get("url") if best else m.get("media_url_https")
            lines.append(f"- {mtype.capitalize()}: {url}")
    return lines


def render(data: dict, quoted: bool = False) -> str:
    user = data.get("user") or {}
    name = user.get("name", "?")
    handle = user.get("screen_name", "?")
    verified = " [verified]" if user.get("is_blue_verified") or user.get("verified") else ""
    prefix = "> " if quoted else ""

    out: list[str] = []
    head = f"{name}{verified} (@{handle}) - {_fmt_ts(data.get('created_at'))}"
    out.append(f"{prefix}**{head}**")
    out.append(prefix)
    body = _expand_text(data)
    for line in (body.splitlines() or [""]):
        out.append(f"{prefix}{line}")

    media = _media_lines(data)
    if media:
        out.append(prefix)
        out.extend(prefix + m for m in media)

    if not quoted:
        favs = data.get("favorite_count")
        replies = data.get("conversation_count")
        stats = []
        if favs is not None:
            stats.append(f"{favs:,} likes")
        if replies is not None:
            stats.append(f"{replies:,} replies")
        if stats:
            out.append("")
            out.append("_" + " - ".join(stats) + "_")

    quoted_tw = data.get("quoted_tweet")
    if quoted_tw and not quoted:
        out.append("")
        out.append("Quoting:")
        out.append(render(quoted_tw, quoted=True))
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python x_tweet.py "<tweet-url-or-id>"')
    tid = extract_id(sys.argv[1])
    if not tid:
        raise SystemExit(f"Could not find a tweet id in: {sys.argv[1]!r}")
    data = fetch_tweet(tid)
    print(f"# Tweet {tid}")
    print(f"Source: https://x.com/{(data.get('user') or {}).get('screen_name','i')}/status/{tid}")
    print()
    print(render(data))


if __name__ == "__main__":
    main()
