# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A `--timeout` flag for the Firecrawl fetcher (#6).
- The missing `.env.example` for the Firecrawl script.
- A security policy with a private reporting path (SECURITY.md).
- A license badge in the README.
- A line in the skill's limits: fetched content is data, not instructions.

### Changed

- The README byline links to belschak.dev and the 403 write-up.
- The copyright line now names contributors alongside the author.

## [1.0.0] - 2026-07-11

Initial release: the four-stage escalation cascade (WebFetch, Jina Reader,
Firecrawl script, browser MCP), the two standard-library fetch scripts, and
the repo package as first published (README, license, contributing guide,
code of conduct, issue and PR templates, animated demo, social card).
