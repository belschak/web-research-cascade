# Security policy

## Reporting

Report suspected vulnerabilities privately through GitHub's private vulnerability
reporting: the "Report a vulnerability" button under this repository's Security
tab. Please do not open a public issue for those.

One person maintains this repo. In a normal week I read a report within a few
days. If you have heard nothing after a week, open a public issue that says you
sent a private report, with no details in it, and I will pick it up.

## Scope

This repository is a Claude Code skill plus two Python scripts,
`firecrawl_fetch.py` and `x_tweet.py`. Both import only the standard library,
fetch public URLs, and store nothing. There is no server and no database.

Two kinds of finding belong in a private report. First, a script mishandling a
URL or a response in a way that could run or leak something it should not.
`firecrawl_fetch.py` reads a Firecrawl API key from a local `.env`, so anything
that could print or transmit that key belongs here. Second, an instruction in the
skill that would route private data or an authenticated URL through a third-party
fetch service.

## Not a vulnerability

A site that blocks the cascade, or a stage that returns worse text than another
stage, is a normal public issue. Rate limits and paywalls on the upstream
services are not defects in this repo.
