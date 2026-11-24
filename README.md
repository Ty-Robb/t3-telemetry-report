# Theo's T3 Code telemetry dump & code assessment

## TL;DR

Reproducible analysis of Theo's 24 Nov 2026 T3 Code product-analytics export (95,789 events) alongside independent source assessments of `pingdotgg/t3code` at [`55085df2`](https://github.com/pingdotgg/t3code/tree/55085df2a6c384f34b37901d5dcbc5925ada1600) by [Codex](reports/codex.md), [Antigravity](reports/antigravity.md), and [Grok](reports/grok.md).

- **No prompts or code in product analytics:** Standard product events carry usage metadata, not prompts, responses, file contents, or local SQLite conversations. Same-day 24 Nov commits removed `~/.codex/auth.json` and `~/.claude.json` account-ID reading, separated mobile relay/analytics IDs, fixed Windows desktop opt-out reading, stripped machine details from relay traces, and marked agent feedback anonymous.
- **Anonymous feedback can still be linked on the wire (reproduced offline):** `agent.feedback` (`anonymous: true`, default off) shares the same `AnalyticsService` queue and `POST /batch/` body as identified install events, contradicting `docs/user/telemetry.md`.
- **Opt-outs are fragmented and have desktop gaps in code:** Product analytics defaults on with no in-app UI toggle (`T3CODE_TELEMETRY_ENABLED=false` only). In source (not live-reproduced in a desktop build), desktop server relay tracing captures `process.env` before deferred shell discovery finishes, and desktop shell discovery omits `T3CODE_OTEL_SDK_DISABLED` and `OTEL_SDK_DISABLED`. Separate channels (default-on mobile crash reports, disconnected hosted web relay traces, and opt-in agent activity publishing, which sends readable project and thread titles) are not controlled by `T3CODE_TELEMETRY_ENABLED`.
- **Correlatable hashes and raw strings remain:** Current code still hashes T3 Connect account IDs with unsalted SHA-256 (one Connect hash links all 16 installs in the published dump). Product events also transmit raw `WSL_DISTRO_NAME`, custom model IDs and relative paths (for example `models/customer-acme.gguf`), mobile device models, and web browser strings.
- **What cannot be verified from source or the dump:** `ingest.t3.codes` server code, IP logging, PostHog/Axiom deployed retention, whether pre-24 Nov OpenAI/Claude account hashes were purged, and third-party AI provider logging.

Start with [CODE-ASSESSMENT.md](CODE-ASSESSMENT.md) for the consolidated findings, [ANALYSIS.md](ANALYSIS.md) for the dump breakdown, or the individual provider reports ([Codex](reports/codex.md), [Antigravity](reports/antigravity.md), [Grok](reports/grok.md); Claude was blocked by API rate limits on both attempted accounts).

---

## Published dump and reproduction

Theo (@theo) published every T3 Code product-analytics event tied to his own installs on 24 Nov 2026
([post](https://x.com/theo/status/2125332535358222808), thread start
[here](https://x.com/theo/status/2125332390239494211)). This repo holds that file exactly as published,
the scripts used to analyse it, and the results.

- `data/t3code-telemetry-events-jsonl-a4896cdc.gz` – the dump as downloaded from
  `https://files.tslop.org/2026/11/t3code-telemetry-events-jsonl-a4896cdc.gz` (via `https://t.co/TJAMjHNuaI`).
  sha256 (gz) `6388379c1c9ea2f814b38960156a51531df7c9db70cf9b511e96bc6b2fd0b39a`,
  sha256 (jsonl) `908d62216800966f870d278ed760c2372bc621b09bde05ecbb6247583f332e47`.
  The uncompressed file (108,971,731 bytes) is over GitHub's 100 MB limit, so only the .gz is committed.
- `scripts/profile.py`, `scripts/analyse.py`, `scripts/extras.py` – Python 3 standard library only.
- `results/` – `profile.txt`, `analysis.json`, `extras.json` produced by the scripts.
- `ANALYSIS.md` – findings and methodology.

```bash
gunzip -k data/t3code-telemetry-events-jsonl-a4896cdc.gz
python3 scripts/profile.py  data/t3code-telemetry-events-jsonl-a4896cdc > results/profile.txt
python3 scripts/analyse.py  data/t3code-telemetry-events-jsonl-a4896cdc results
python3 scripts/extras.py   data/t3code-telemetry-events-jsonl-a4896cdc results
```

## Independent code assessments

[CODE-ASSESSMENT.md](CODE-ASSESSMENT.md) traces T3 Code's implementation, data destinations, opt-outs, and privacy limitations. It links the actual provider reports and records unavailable providers. The original dump and generated aggregates are unchanged; `ANALYSIS.md` now corrects interpretation errors found during review.
