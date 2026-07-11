---
name: web-research-cascade
description: A robust web-fetch cascade so that blocked primary sources still get read instead of being silently skipped. Use this skill whenever a URL is fetched, a page needs to be researched, or WebFetch/WebSearch returns a 403/401/429/"unable to fetch"/empty body/CAPTCHA. Also use it for any analysis or comparison research where primary sources matter (not just secondary blogs), and on "read this page", "what does X say", "research Y", "look at this". Cascade: WebFetch, then Jina Reader, then a Firecrawl script (sparingly), then Chrome (browser MCP). Also covers Reddit (threads, subreddits, search) and single X/Twitter tweets, which need their own route instead of the generic cascade. Core rule: a good but blocked source is opened via the cascade, NEVER swapped for a weaker error-free one.
---

This skill exists because the built-in WebFetch returns a 403 or an empty/CAPTCHA body on many primary sources, and the agent then quietly falls back to a weaker secondary source. The result: your analysis rests on blogs that write *about* the source instead of the source itself. The cascade prevents exactly that.

## Search vs. fetch

**Search** (which sources exist on topic X?): use your built-in web search as the default. **Fetch** (read one known URL): the cascade below. Do not confuse the two.

## Work order: sources first, then transport

Step 0, before any fetching: decide which sources would genuinely best answer the question (the primary document, the official docs, the original announcement), not whichever page is easiest to fetch. Source quality beats fetch convenience. Then get exactly those sources: if one of them blocks, open it via the cascade instead of swapping it for a weaker error-free source just because that one did not throw a 403. A 403 is a transport problem, not a reason to drop the source. Only when every stage fails may a source count as "unreachable", and then you say so explicitly instead of papering over it.

## Sources with their own route (check BEFORE the cascade)

Reddit and X block the public stages (Jina) wholesale because they demand a logged-in/OAuth session and reject datacenter IPs. The generic cascade is not worth it for them; they have a shorter, cleaner path. Check this branch FIRST before running a `reddit.com` or `x.com` URL through the cascade.

**Reddit (`reddit.com`, `redd.it`, `old.reddit.com`).** The official Data API now requires manual pre-approval under Reddit's "Responsible Builder Policy" (late 2025, roughly a week-long review), so self-service keys are effectively gone, and a raw `.json` fetch via script/WebFetch/Jina/Firecrawl returns 403 (Reddit blocks anything without a real browser fingerprint + cookies). Working path: **browser MCP + the `.json` route** using your logged-in session. Append `.json` to the Reddit URL, navigate a browser tab there, read it with the page-text tool, and turn the JSON into Markdown:
```
Thread:    https://www.reddit.com/r/<sub>/comments/<id>.json?limit=20&sort=top   -> post + comments
Subreddit: https://www.reddit.com/r/<sub>/top.json?t=week&limit=15                -> listing
Search:    https://www.reddit.com/r/<sub>/search.json?q=<query>&restrict_sr=1&sort=relevance   (or /search.json?q=... site-wide)
```
If the JSON is too large/unwieldy, read the normal HTML page in the browser tab instead. Both need a real logged-in browser session (datacenter IPs are hard-blocked).

**X / Twitter (`x.com`, `twitter.com`).** No free API royal road. Two cases:
- **A single public tweet** -> helper over the no-auth syndication route (the same one X uses for embeds):
```
python ~/.claude/skills/web-research-cascade/x_tweet.py "<tweet-url-or-id>"
```
Returns Markdown (author, text with resolved t.co links, media, likes/replies). The route is unofficial and can close without warning; on a 404/error fall back to the browser (stage 4).
- **A thread, profile, search, or protected tweets** -> no free route; go straight to stage 4 (browser MCP with your login). Do not grind through stages 1-2, they fetch nothing there.

**Zendesk-based docs pages (URL contains `/hc/en-us/articles/{ID}-`).** On 403/404 skip the cascade; the Help Center API returns the article directly as JSON:
```
{base_url}/api/v2/help_center/en-us/articles/{ID}.json   -> article HTML in the "body" field
```

## The cascade (per URL, in this order)

**Stage 1: WebFetch directly.** The fastest path, and it works for most pages that load anyway. Only escalate when it blocks.

**Stage 2: Jina Reader.** Prepend `https://r.jina.ai/` to the full target URL and fetch that with WebFetch:
```
https://r.jina.ai/https://www.example.com/article
```
Jina fetches the page from its own servers (a real IP instead of a datacenter one) and returns clean Markdown. Keyless, free, no counter, only a ~20 requests/minute pace limit. It solves the most common cause (datacenter-IP block) and JS-heavy pages. Verified: a page that WebFetch refuses with a 403 comes through Jina in full.

**Stage 3: Firecrawl script (use SPARINGLY).** When Jina fails on a public page (hard Cloudflare/bot wall, no login required), fetch it via the local script:
```
python ~/.claude/skills/web-research-cascade/firecrawl_fetch.py "https://www.example.com/article"
```
Residential proxy + real fingerprint; beats casual 403s. Scrape only (1 credit), free tier ~1000 credits/month (resets monthly), never for search (use built-in web search), never for routine/bulk fetches, only the one blocked single fetch. The key lives in `.env` (gitignored). See `.env.example` for setup.

**Stage 4: Browser (the user's logged-in session).** When even Firecrawl is not enough (real login, CAPTCHA, a page tied to the user's account, a hard Turnstile wall), open the page via a browser MCP that sees the user's real browser session, for example Claude in Chrome or Playwright attached to the user's own Chrome profile over CDP. The agent then reads the page through the user's own account, seeing exactly what the user would see in their browser; only this path sees logged-in content. Guardrails: only the user's own accounts and sessions, and never navigate to or screenshot pages that display secrets (API-key pages, token settings), because page content can end up in the transcript.

## Straight to stage 4 on login content

Pages that require login by definition (your accounts, paywalled subscriptions, university/tax portals) should NOT be dragged through stages 1-3. Go straight to the browser MCP. The public stages (including Firecrawl) can fetch nothing there.

## What counts as a block (escalation triggers)

HTTP 403/401/429, "unable to fetch", an empty or obviously truncated body, a CAPTCHA / "log in to continue" message in the content, or content that is clearly not the actual page.

## Limits and exceptions

- **GitHub: always via the `gh` CLI**, never through the cascade (authenticated, JSON, cleaner).
- **Privacy:** only public URLs go through Jina. Never send a URL with a token/session/secret in its path through Jina; those go through the browser MCP.
- **Close browser tabs** after research so you never leave tabs open for the user to clean up.
- **Firecrawl runs as a script (stage 3), not as an MCP.** The Firecrawl MCP injects a "firecrawl_search = primary search tool" instruction that overrides the cascade, and Claude Code currently offers no configuration to suppress what an MCP server injects (a request to make MCP injection suppressible was closed "not planned": GitHub anthropics/claude-code#43690). The script has no such instruction and costs no standing context. Scrape only (1 credit), free tier ~1000/month, sparing use.
