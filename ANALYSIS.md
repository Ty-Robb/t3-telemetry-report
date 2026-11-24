# Findings: Theo's T3 Code telemetry dump

Analysed 24 Nov 2026 (UK time). All figures come from `results/*.json`; nothing is estimated unless marked.

## What it is
- PostHog-style product-analytics export from T3 Code (pingdotgg/t3code). Each line: `uuid, event, distinct_id,
  timestamp, received_at, inserted_at, properties (JSON string), user_agent, to_posthog`.
- 95,789 events (matches Theo's stated count), 108.97 MB uncompressed, 6.06 MB gzipped.
- Event timestamps 2026-09-04 10:48 to 2026-11-24 17:28 (assumed UTC): 82 calendar days, events on all 82.
  `received_at` trails `timestamp` by a median of ~5 s even for September events, while `inserted_at` starts 2026-10-03, so ingest received them live and loaded the export table later.
- 16 event types, 103 distinct property keys, 14 `distinct_id`s, 16 `installId`s, 15 `ownerId`s.

## Event types
| event | count |
|---|---:|
| provider.turn.completed | 40,460 |
| provider.request.completed | 16,409 |
| mcp.tool.invoked | 12,109 |
| client.connected | 9,085 |
| mcp.delegated_task.finished | 6,786 |
| client.turn.requested | 4,760 |
| install.owner_observed | 2,660 |
| feature.used | 1,545 |
| client.thread.started | 914 |
| server.boot.heartbeat | 899 |
| other 6 types | 162 |

## What the data says about his usage
- Providers (turns completed): Claude agent 23,538, Codex 13,961, Antigravity 1,659, Muse 1,267, Grok 29, pi 4, opencode 2.
- Top models on events: claude-opus-5-5 24,922; claude-fable-5-2 5,367; gpt-6.1-sol 3,404; gpt-6-astra 1,801.
- Effort: high 23,884, xhigh 9,366, max 3,924. Runtime mode: full-access 56,787 of 56,908.
- Tokens on `provider.turn.completed`: 203.3B input, of which 199.7B cached (98.2%); 0.61B output; 0.23B reasoning.
  Codex 110.0B input, Claude 88.4B. Single biggest turn: 880.8M input tokens (Codex, with subagents).
- Heavy agent orchestration: 6,186 `delegate_task` calls; 45,505 turn/request events carrying `createdBy`, 41,211 attributed to an agent vs 4,294 to the user. These are not counts of distinct threads.
  Claude delegates most: claude→claude 2,813, claude→codex 1,598, claude→muse 844, claude→antigravity 698.
- Ramp-up: under 500 events/week in September, then 23,396 in the week of 19 Oct.
- Server OS: Linux 71,213 events, macOS 17,318, Windows 7,258. `client.connected` events with a connection method: relay 4,676, direct 199, ssh 2. The previous 8,885/1,597/2 totals mixed connections, thread starts, and turn requests.
- Phones/tablets: iOS 1,472 events and Android 104, with device models iPhone19,3, "iPhone Duo", iPhone 18 Pro Max, iPhone18,2, SM-F971U1.
- Tool errors: 1,596 of 12,109 MCP tool calls (13.2%), led by `unknown` 821 and `OrchestratorMcpFailure` 540.

## Privacy assessment
The scanner found no matches for its email, IPv4, selected path, URL, or long-text patterns in top-level property strings and `user_agent`. This is a limited pattern scan, not proof that all personal information is absent. No prompt or response fields were identified in this export. Custom model IDs and device labels also appear; strings are not all closed enums or hashes. See [the code assessment](CODE-ASSESSMENT.md) for data paths outside this export.

What IS there and worth noting:
1. Account-derived hashes. 542 `install.owner_observed` events have `ownerSource` `openai` (278) or `claude` (264).
   In the source before commit 84e4264 (merged 24 Nov 2026), `install.owner_observed` hashed the OpenAI `user_id`
   from the unverified `id_token` or Claude `oauthAccount.accountUuid`, while legacy `distinct_id` hashed Codex
   `account_id` (shared across a ChatGPT Team) or Claude `userID` (random per machine), read from
   `~/.codex/auth.json` and `~/.claude.json` and hashed with no salt
   (`packages/shared/src/telemetryId.ts`). Unsalted means anyone holding the raw account ID can recompute and match it,
   and the same hash lines up across datasets. Not reversible by guessing, because the inputs are random IDs.
2. Cross-machine linking. One legacy `distinct_id` (43ee99…) appears on macOS, Linux and Windows servers, because the
   old `distinct_id` came from the Codex account. That is how one person's machines were tied together.
3. Daily rhythm. User-sent turns (`client.turn.requested`) by UTC hour: 0 between 15:00 and 16:59, 2 at 17:00, 38 at 14:00,
   vs 300–400 an hour from 06:00 to 11:00. Ms-precision timestamps reveal when someone is at the keyboard.
   (The "sleep issues" reply in the thread is reading exactly this.)
4. Device fingerprint. Exact phone model codes, OS major version, CPU arch, project and thread counts and 125 nightly build
   versions together narrow an install down a lot, even with no name.
5. Scope of "100%". This is the product-event stream only. At commit `11edf884` (before `dc7b880`), the project's docs said
   relay connection traces go to Axiom separately and "can include connection timings, environment identifiers and the
   connected machine's name". Commit `dc7b880` later removed machine details from relay traces and updated `docs/user/telemetry.md`.
   Those traces are not in this dump. Whether the ingest endpoint logs IP addresses is not visible here.
6. Dev/test data is mixed in: models such as `claude-nonexistent-9` and `agy-demo` appear, consistent with Theo developing T3 Code.

## Code changes the same day (pingdotgg/t3code, 24 Nov 2026)
- 4eccb0e "relay traces no longer record callers' IP addresses or user agents".
- 3380585 "delete a user's relay data when Clerk deletes the user".
- 84e4264 "analytics no longer reads or sends Codex and Claude account IDs" (ownerSource now only `connect`/`device`).
- 482e197 "mobile: analytics uses its own random device id".
- 3ba003b "Windows desktop applies the saved user telemetry opt-out" (the opt-out was not applied there before).
- 796103f "agent feedback no longer links to the install".
- dc7b880 "respect relay tracing opt-outs and remove machine details" (merged after `11edf884`; updates relay tracing and `docs/user/telemetry.md`).

## Multi-model assessment
The original analysis did not run other providers. Independent code assessments are now tracked in [CODE-ASSESSMENT.md](CODE-ASSESSMENT.md), with actual provider identities, revision pins, evidence limits, and unavailable providers recorded separately.

## Appendix: Methodology
1. Question: what can be learned from Theo's published T3 Code event dump, and is anything in it identifying or sensitive?
   Scope: only this file, plus the public t3code repo for how IDs were derived.
2. Sources: the dump (primary, URL and hashes above, downloaded 24 Nov 2026 ~21:08 UK); Theo's posts 2125332390239494211 and
   2125332535358222808 (primary, via X API); github.com/pingdotgg/t3code at commit 11edf884 (primary; files
   `apps/server/src/telemetry/Identify.ts`, `packages/shared/src/telemetryId.ts`, `docs/user/telemetry.md`,
   `docs/internals/08_product-analytics.md`).
3. Retrieval: `curl -sIL https://t.co/TJAMjHNuaI`, `curl -sL -o … https://files.tslop.org/2026/11/t3code-telemetry-events-jsonl-a4896cdc.gz`,
   `git clone --depth 50 https://github.com/pingdotgg/t3code.git`, `git show 84e4264b`.
4. Processing: each line parsed as JSON; `properties` parsed as a second JSON string. No rows dropped. Week buckets start Monday.
   Uncached input = inputTokens − cachedInputTokens. PII scan regexes are in `scripts/analyse.py`.
5. Assumptions: `timestamp` is UTC (PostHog convention, not stated in the file). `cachedInputTokens` is a subset of
   `inputTokens` (checked: on all 38,901 turns that carry both fields, cached never exceeds input). Token counts are as the provider reported them;
   1,559 `provider.turn.completed` events had `usageStatus` unavailable and 1,418 partial, so totals are a floor.
6. Limitations: one user's data; cannot show what other users' events look like, what the ingest server logs (IP), or the
   Axiom traces. Confidence: event counts and schema high; privacy-of-content finding high for this file; hash-derivation
   finding high (read from source); daily-rhythm reading medium (depends on the UTC assumption and agents running unattended).
7. Reproduce: Python 3.10+, no packages. Run the four commands in README; compare `rows 95789`, `distinct_ids 14`,
   `provider.turn.completed 40460`, total inputTokens 203,305,106,680.
8. Open questions: does ingest.t3.codes store client IPs; what retention applies to the PostHog copy and to Axiom traces;
   whether old account-derived hashes will be deleted or re-keyed now that 84e4264 has merged.

## Follow-up verification

The original scripts and both dump hashes reproduced exactly. The code assessment corrected the thread-count interpretation, connection-method scope, turn-only usage-status counts, "other 6 types" sum (162, not 164), `received_at` vs `inserted_at` timing, historical account-hash input split (`owner_observed` vs legacy `distinct_id`), and additional 24 Nov relay commits (`4eccb0e`, `3380585`, `dc7b880`) above. A single `connect` owner hash occurs across all 16 install IDs in the dump and a single `device` owner hash occurs across 15 installs; current source retains both. The export also contains 100 rows marked `to_posthog: false`. These observations do not establish receiver retention or logging policy. See [verification results](results/code-assessment/corrections.json).
