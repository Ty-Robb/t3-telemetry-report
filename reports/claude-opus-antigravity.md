# Independent assessment: T3 Code telemetry and the `t3-telemetry-report` baseline

## Review note

Claude Opus 5.5 (`claude-opus-5-5`) authored this assessment independently through the `antigravity` harness. Antigravity (Gemini 4 Neon) verified all 122 pinned GitHub permalinks (start and end lines, including parent commits) and spot-checked the newly surfaced findings (`linkEnvironment.ts#L238-L252` auto-enabling `publishAgentActivity: true`, `SettingsPanels.tsx#L2589` and `privacy-policy.astro#L85-L88` calling telemetry "anonymous", and `other 6 types = 162`). One cross-check note on Part 2.5: on hosted web (`apps/web/src/cloud/publicConfig.ts#L79`), relay tracing defaults on with no client toggle while disconnected or before a server answers, and honors `relayTracingAllowed: false` once connected to an opted-out server via `setServerRelayTelemetry` (`apps/web/src/appInit.tsx#L281`).

## Provenance

- **Assessor:** Claude Opus 5.5 (`claude-opus-5-5`), a real model run, not a simulated opinion.
- **Harness:** Antigravity (`providerInstanceId: antigravity`). This assessment did **not** run on the `claudeAgent` harness.
- **Independence:** I did the work myself, with no subagents. I did not read `provider-drafts/`, `report-repo/reports/`, `report-repo/CODE-ASSESSMENT.md`, `report-repo/results/code-assessment/`, or the workspace `verification/` folder.
- **Date:** 2026-11-24 (UTC).
- **Pinned inputs:**
  - T3 Code: `pingdotgg/t3code` at `55085df2a6c384f34b37901d5dcbc5925ada1600` (shallow clone, 100 commits, boundary commit `b51399fb3899e35aebbcdd56d1c63eca5672fac2`, all commits dated 2026-11-24).
  - Report baseline: `Ty-Robb/t3-telemetry-report` at `b68d58700de22718792327151de0e7ec6b3d8732` (`ANALYSIS.md`, `README.md`, `scripts/*`).
  - Dump: `data/t3code-telemetry-events-jsonl-a4896cdc.gz`. `results/*` is byte-identical between the baseline commit and the report repo HEAD (checked with `git diff --stat`).
- **Access limits I kept:** read-only. I did not access live user data, auth files, credentials, conversations, local databases, or the network. The only file I wrote is this report.

## Evidence labels

Each claim carries one of these labels:

- **[DUMP]** observed in the published dump.
- **[CODE]** code-defined behavior at `55085df2` or at a named parent commit. This shows what the source does. It does not prove what any installed build runs.
- **[DOC]** a claim in repo documentation, UI copy, or the privacy policy.
- **[UNKNOWN]** hosted, deployed, or provider-side behavior that neither the code nor the dump shows: ingest IP logging, PostHog or Axiom retention, live traffic, provider retention.

## Summary

1. **The dump checks out [DUMP].** Both SHA-256 hashes, the row count (95,789), the byte size (108,971,731), the 16 event types, 103 property keys, 14 `distinct_id`s, 16 `installId`s and 15 `ownerId`s all match `ANALYSIS.md`. A broader string scan than the report's found no emails, file paths, URLs, IP addresses or free text. The report's "no content" conclusion holds for this file.
2. **The report misses the biggest linkage in the dump [DUMP][CODE].** One `connect` owner hash (`bc4d2382…`) appears on **all 16 installs** and 13 of the 14 `distinct_id`s. One `device` owner hash (`148bd960…`) appears on 15 installs. These come from the T3 Connect account and the client device, and the code still sends both at HEAD. Cross-machine linking is how the current code is designed to work. It is not only a legacy `distinct_id` artifact, as `ANALYSIS.md` suggests.
3. **At HEAD, product analytics are pseudonymous, not anonymous [CODE][DOC].** The `connect` owner is an unsalted SHA-256 of the T3 Connect account ID. Anyone who holds the raw account ID, including the operator of the account system, can recompute it and join it to account records. The settings UI and the privacy policy still call the data "anonymous". Whether anyone actually performs that join is [UNKNOWN].
4. **"Unlinkable" agent feedback is only unlinkable inside the event payload [CODE].** `agent.feedback` goes out with a per-event `distinct_id` and no `installId`. But it travels in the same HTTP batch as identified events, from the same host, with the same host dimensions. The docs say reports "cannot be tied to your installation", which overstates this.
5. **Several opt-out gaps and defaults are worth stating [CODE][DOC]:**
   - Product analytics and server relay tracing have no in-app toggle. Only an environment variable or a managed policy turns them off.
   - Mobile crash reporting is on by default.
   - The hosted web app has no tracing toggle.
   - Linking an environment from the mobile app turns on agent-activity publishing (project and thread titles) automatically. The telemetry opt-out does not cover it.
   - I also found a likely timing gap: on the desktop app, server relay tracing may not honor a shell-profile opt-out on the first launch after it is set.
6. **Seven privacy fixes landed in the shallow clone on 2026-11-24, all after the newest dump event [CODE].** The newest event is at 17:28 UTC; the earliest fix is at 19:57 UTC. So the dump shows only pre-fix behavior. `ANALYSIS.md` lists four of these fixes and omits three that affect relay traces and relay data.

## Method

- **Dump:** I streamed the gzip through Python standard-library one-liners, with no intermediate files. I recomputed every figure in `ANALYSIS.md` and added checks on identifier linkage, owner sources, ingest metadata fields, and free-form strings.
- **Code:** I used `git grep` and file reads at `55085df2`. I traced every `AnalyticsService.record` caller, the identity and owner sources, client connection parameters, relay tracing gates, mobile observability, agent feedback, agent-activity publishing, and local storage paths. For history, I read the diffs of the same-day commits and the file contents at their parents.
- **Docs:** `docs/user/telemetry.md`, `docs/internals/08_product-analytics.md`, `docs/user/managed-policy.md`, `docs/user/text-generation.md`, the settings UI string, and the marketing privacy policy.
- **Not done:** I did not run the T3 Code test suite or the report's scripts, to avoid writing any files. I did not inspect live traffic or deployed services.

## Part 1. Accuracy of `ANALYSIS.md` at `b68d5870`

### 1.1 Dump verification [DUMP]

| Check | ANALYSIS.md | Recomputed |
|---|---|---|
| sha256 (gz) | `6388379c…0b39a` | match |
| sha256 (jsonl) | `908d6221…2e47` | match |
| rows / bytes | 95,789 / 108,971,731 | match |
| event types / property keys | 16 / 103 | match |
| distinct_id / installId / ownerId | 14 / 16 / 15 | match |
| turns by provider | claudeAgent 23,538, codex 13,961, … | match |
| input / cached / output / reasoning tokens | 203.3B / 199.7B (98.2%) / 0.61B / 0.23B | match (203,305,106,680 input) |
| Codex / Claude input | 110.0B / 88.4B | match |
| largest turn | 880.8M, Codex, with subagents | match (880,840,530, `hasSubagents: true`) |
| delegate_task calls | 6,186 | match |
| MCP tool errors | 1,596 of 12,109; `unknown` 821, `OrchestratorMcpFailure` 540 | match |
| "other 6 types" | 164 | **162** (61 + 42 + 28 + 27 + 2 + 2) |
| usageStatus "turns" unavailable / partial | 2,611 / 2,091 | **turns only: 1,559 / 1,418**. 2,611 / 2,091 is turn plus request events combined. |

### 1.2 Concrete corrections to `ANALYSIS.md`

Line numbers refer to the [baseline ANALYSIS.md](https://github.com/Ty-Robb/t3-telemetry-report/blob/b68d58700de22718792327151de0e7ec6b3d8732/ANALYSIS.md).

1. **L6, "PostHog-style export".** The rows carry `received_at`, `inserted_at`, `user_agent` and `to_posthog`. That fits an export from T3's own ingest store, which keeps events and forwards them to PostHog. The code comment at [AnalyticsService.ts#L1](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L1-L1) and [telemetry.md#L6-L7](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L6-L7) say the same [CODE][DOC]. 100 `mcp.tool.invoked` events from 2026-10-24 have `to_posthog: false`. `ANALYSIS.md` does not mention this, though `results/analysis.json` records it [DUMP].
2. **L10, "September events were backfilled".** The data does not support client backfill. `received_at` trails `timestamp` by a median of 5 s and a p99 of 11 s (maximum 5,004 s). All 1,417 events before 2026-10-03 have `inserted_at` on 2026-10-03 [DUMP]. So ingest received them live, and the export table was loaded later.
3. **L26.** Change "other 6 types 164" to **162**.
4. **L30, "Top models on events".** These counts sum the `model` field over turn, request and other events, so the same work is counted more than once. Present them as event counts, not model usage.
5. **L34, "45,505 thread-creating events, 41,211 created by an agent vs 4,294 by the user".** This is mislabeled. `createdBy` appears on 29,096 `provider.turn.completed` and all 16,409 `provider.request.completed` events [DUMP]. It records who started the run's first message ([ProviderUsageAnalytics.ts#L34-L44](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L34-L44)) [CODE], not thread creation. Turn and request events also describe overlapping work, so summing them double-counts.
6. **L37, "Clients via relay 8,885, direct 1,597, ssh 2".** These are **events**, not clients: relay = `client.connected` 4,676 + `client.turn.requested` 3,567 + `client.thread.started` 642 [DUMP].
7. **L43, "Every string field is a closed enum, a version, a model ID or a hash".** Partly wrong.
   - In the dump: `clientAppVersion` includes free-form values such as `3.0.0`, `clientDeviceModel` includes marketing names such as `iPhone Duo`, and `model` includes custom IDs such as `vibeproxy/gpt-6-luna` and `restful-walrus` [DUMP].
   - In the code: the server accepts client-supplied `clientAppVersion`, `clientBrowser` and `clientDeviceModel` with only length limits ([ws.ts#L832-L874](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L832-L874)). It passes custom model IDs through, reducing only file paths to a file name ([ProviderDimensions.ts#L27-L50](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderDimensions.ts#L27-L50)). It also sends the WSL distro name as `wsl` and `serverWslDistro` ([AnalyticsService.ts#L221-L228](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L221-L228)) [CODE]. The dump has no WSL events.
   - The PII scan regex in [analyse.py#L66](https://github.com/Ty-Robb/t3-telemetry-report/blob/b68d58700de22718792327151de0e7ec6b3d8732/scripts/analyse.py#L66-L66) only matches a literal double backslash for Windows paths, so a normal path such as `C:\Data\x` would not match. Its only other path patterns are the macOS and Linux home prefixes and `~/`.
   - My broader scan, for any `/`, `\`, `@`, `:` or whitespace in any non-hash string, found only the two proxied model IDs and two device names above. The report's conclusion stands; its stated basis is too strong.
8. **L47 to L51, how the provider-account hashes were derived.** The report conflates two different values. At parent `54ba2408f452705a5e43ce3dbdc878b6eeefded4` [CODE]:
   - The **`openai` owner** was the SHA-256 of the OpenAI `user_id` claim in the Codex `id_token` ([Identify.ts@54ba2408#L44-L46](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L44-L46), [#L181-L186](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L181-L186), [#L321-L338](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L321-L338)). It was read from `~/.codex/auth.json` and **also from T3's own stored ChatGPT credentials** ([CodexChatGptAuth.ts@54ba2408#L289-L300](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/provider/CodexChatGptAuth.ts#L289-L300)).
   - The **`claude` owner** was `oauthAccount.accountUuid` from `~/.claude.json`.
   - **`distinct_id`**, not the owner, used the Codex `tokens.account_id` first, then Claude `userID`, then the install ID ([#L274-L292](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L274-L292)). The code's own comment says `account_id` is a ChatGPT workspace that a whole Team shares ([#L18-L31](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L18-L31)). So a legacy `distinct_id` could merge several people.
9. **L52 and L53, cross-machine linking.** The report attributes this only to the legacy `distinct_id` (`43ee99…`). The dump shows a stronger and still-current mechanism [DUMP]:

   | owner source | ownerId prefix | installs | distinct_ids |
   |---|---|---:|---:|
   | connect | `bc4d2382` | 16 of 16 | 13 of 14 |
   | device | `148bd960` | 15 | 12 |
   | device | `b3d92cfc` | 14 | 11 |
   | device | `518615ac` | 13 | 10 |
   | claude | `3531bf70` | 5 | 2 |
   | openai | `a6e59d2b` | 4 | 1 |

   - The code still sends `connect` and `device` owners at HEAD (section 2.3). Calling `43ee99…` "the Codex account" is an inference. The code allows Codex `account_id` or Claude `userID`, and the former can be shared by a Team.
   - Two installs changed `distinct_id` mid-stream: `f75637…` (from `43ee99…` to `e25f82…`) and `e804e0…`, whose first `distinct_id` equals its install ID before switching to `759117…`.
   - 9,467 events from four `distinct_id`s carry no `installId` at all. These are from older builds, with the last one on 2026-11-06.
10. **L54 and L55 (and L85), the UTC assumption.** The code supports it. `timestamp` is the client-side `capturedAt`, set with `DateTime.formatIso(now)` ([AnalyticsService.ts#L177-L186](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L177-L186), sent at [#L232](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L232-L232)) [CODE]. It is the host's clock, not the server's. Minor point: 06:00 UTC has 288 user turns, slightly below the stated "300 to 400" [DUMP].
11. **L59 to L61, the relay trace quote.** The quote is from the docs at `11edf884` ([telemetry.md@11edf884#L68-L71](https://github.com/pingdotgg/t3code/blob/11edf884bc7d8332a69cc2faa563ce91e33bc1da/docs/user/telemetry.md#L68-L71)), which also said failed spans could include error messages and stack traces. Commit `dc7b8802` changed both the code and the docs later that day. At HEAD the docs say traces carry timings, request paths, environment and thread identifiers, and error types, and omit machine addresses, query strings, log lines, error messages and stack frames ([telemetry.md#L66-L71](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L66-L71)) [DOC].
    - The report misses that relay-side traces recorded **caller IP addresses and user agents** until `4eccb0ec` ([Api.ts@c39c21f8#L234-L243](https://github.com/pingdotgg/t3code/blob/c39c21f870fa75b51c11ef9bec67fcd1a96dc14a/infra/relay/src/http/Api.ts#L234-L243)) [CODE].
    - It also misses that the dump itself shows ingest records the HTTP `User-Agent` per event (`node` on 60,434 events, empty on 35,355) [DUMP]. That proves the ingest stores some request metadata. Whether it stores IPs is still [UNKNOWN].
12. **L64 to L68, same-day commits.** Add `4eccb0ec` (relay traces drop IP and user agent), `dc7b8802` (relay tracing honors opt-outs and drops machine details), and `3380585e` (relay data is deleted when Clerk deletes the user). The precise bug behind `3ba003be`: the Windows desktop read `T3CODE_TELEMETRY_ENABLED` only from its own process scope. It did not read the variable when it was saved at User or Machine scope ([DesktopShellEnvironment.ts@482e197f#L132](https://github.com/pingdotgg/t3code/blob/482e197faeb5dfef69582514bf14769fa019a71a/apps/desktop/src/shell/DesktopShellEnvironment.ts#L132-L132) versus [HEAD#L132-L137](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/desktop/src/shell/DesktopShellEnvironment.ts#L132-L137)).
13. **L78, "current" source.** `11edf884` is a descendant of `84e4264b`, so the "current" source the report read already had the account-ID fix. That is consistent with its use of `git show 84e4264b`, but worth saying explicitly.
14. **Omissions.** The report does not cover:
    - `$process_person_profile: false` on all 95,789 events [DUMP].
    - Events the code emits that the dump lacks: `agent.feedback`, `chatgpt.auth.started` and `.completed`, `chatgpt.transfer.started` and `.completed`.
    - Events in the dump that HEAD no longer emits: `client.connected`, `provider.session.*`, `provider.turn.sent`, `provider.runtime_mode.changed`, `provider.request.responded`.
    - Mobile crash reports, agent-activity publishing, agent feedback, and local storage.

## Part 2. What T3 Code gathers at `55085df2` (product analytics)

### 2.1 Transport and destination [CODE]

- **Who sends:** only the server. It does a JSON `POST` to `${T3CODE_POSTHOG_HOST}/batch/`. The default host is `https://ingest.t3.codes` and a public PostHog project key is the default ([AnalyticsService.ts#L69-L82](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L69-L82), [#L205-L242](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L205-L242)).
- **Batching:** 20 events per batch, a 1,000-event buffer, a flush every 10 s, retries for up to 30 min, and a 1 s flush at shutdown ([#L44-L61](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L44-L61), [#L365-L371](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L365-L371)).
- **Clients:** web, desktop renderer and mobile never load a PostHog SDK. `git grep` finds no PostHog or ingest references outside the server, apart from an unrelated Linear schema. The only third-party observability dependency is `expo-observe`, in mobile. The internal doc says the same ([08_product-analytics.md#L3-L5](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/internals/08_product-analytics.md#L3-L5)).
- **Retention and forwarding:** the ingest keeps a copy and forwards to PostHog [DOC] ([telemetry.md#L3-L7](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L3-L7)). Retention periods and IP handling at the ingest and at PostHog are [UNKNOWN]. The privacy policy states no retention period for product usage data ([privacy-policy.astro#L361-L369](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/marketing/src/pages/privacy-policy.astro#L361-L369)).

### 2.2 Properties on every event [CODE]

The server adds these to every event ([AnalyticsService.ts#L210-L234](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L210-L234)):

- `uuid` (UUIDv7) and `timestamp` (ms precision)
- `distinct_id` and `installId`
- `$process_person_profile: false`
- `platform`, `arch`, `serverOs`, `serverArch`
- `wsl` and `serverWslDistro` (free-form `WSL_DISTRO_NAME`)
- `t3CodeVersion`, `serverAppVersion`, `telemetryChannel`
- `clientType`, `serverMode`

### 2.3 Identifiers, hashing and linkability [CODE]

All IDs pass through one helper: plain, **unsalted** SHA-256, hex-encoded ([telemetryId.ts#L4-L12](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/telemetryId.ts#L4-L12)).

| ID | Source | Linkability |
|---|---|---|
| `distinct_id` = `installId` | SHA-256 of a random UUIDv4 in `<state>/anonymous-id` ([Identify.ts#L103-L145](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/Identify.ts#L103-L145)) | Stable per state directory. No provider input since `84e4264b`. |
| `connect` owner | SHA-256 of the linked T3 Connect user ID. The server reads it from its secret store ([Identify.ts#L147-L164](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/Identify.ts#L147-L164)). Every client also sends `hashTelemetryId(accountId)` as `clientOwner` ([remote.ts#L45-L63](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/authorization/remote.ts#L45-L63)). | The same value on every install and surface for one account. The comment says this is on purpose ([telemetryId.ts#L4-L7](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/telemetryId.ts#L4-L7)). Anyone who holds the raw account ID can recompute it. |
| `device` owner | SHA-256 of a random per-client ID: web `localStorage` ([platform.ts#L351-L364](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/connection/platform.ts#L351-L364)), mobile secure storage ([mobile-storage.ts#L69](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/persistence/mobile-storage.ts#L69-L69), [platform.ts#L193-L194](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/connection/platform.ts#L193-L194)) | Built to link "two environments opened from one device … even when nobody is signed in" ([capabilities.ts#L43-L52](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/platform/capabilities.ts#L43-L52)). |

- **How owners reach analytics:** clients put the owner hashes in the WebSocket URL query (`clientOwner`, `clientDevice`) ([remote.ts#L108-L113](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/authorization/remote.ts#L108-L113)). The server accepts only 64-hex values ([ws.ts#L876-L896](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L876-L896)). It records `install.owner_observed` once per owner per process, capped at 1,000 per observer ([AnalyticsService.ts#L342-L363](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L342-L363), [serverRuntimeStartup.ts#L174-L178](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/serverRuntimeStartup.ts#L174-L178)).
- **Consequence:** a client connecting to any environment it is authorized for gives that environment's analytics its own account and device hashes. Whether relay-side spans record these query strings is [UNKNOWN]. Relay monitoring queries do read `attributes.url.full` ([monitoring.ts#L343](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/monitoring.ts#L343-L343)), but I did not confirm that the environment WebSocket URL passes through a traced relay request.
- **Naming mismatch [DOC]:** the settings page calls this "anonymous usage data" ([SettingsPanels.tsx#L2589](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/components/settings/SettingsPanels.tsx#L2589-L2589)), and so does the privacy policy ([privacy-policy.astro#L85-L88](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/marketing/src/pages/privacy-policy.astro#L85-L88)). With a stable install ID and an unsalted account hash, the data is pseudonymous. The user doc describes the account hash accurately ([telemetry.md#L3-L7](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L3-L7)).

### 2.4 Complete event inventory at HEAD [CODE]

I found every `record(` caller of `AnalyticsService` with `git grep -n "AnalyticsService"` and read each call site.

| Event | Emitted at | Event-specific properties |
|---|---|---|
| `provider.turn.completed` | [ProviderUsageAnalytics.ts#L412-L418](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L412-L418) | `reportVersion`, `provider` (driver kind), `terminalStatus`, `usageStatus`, `usageScope`, `usageReported`, `hasSubagents`, token counters, `localCommand`, `other*Tokens`, `model`, `effort` (allow-list), `serviceTier`, `runtimeMode`, `interactionMode`, `createdBy`, `creationSource`, `scheduled`, `subagent`, `mixedModels`, `observedModel`, `segment`, `childKind`, `durationMs` ([#L174-L205](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L174-L205)) |
| `provider.request.completed` | [#L419-L423](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L419-L423) | run-level rollup with `requestKind`, `lifecycleObserved`, `providerTurns`, `continuations`, `steeringRestarts`, `child*` fields ([#L333-L370](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L333-L370)) |
| `mcp.tool.invoked` | [McpHttpServer.ts#L1165-L1189](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/mcp/McpHttpServer.ts#L1165-L1189) | `tool`, `caller*`, `target*`, `crossProvider`, `outcome`, `errorCode`, handoff settings ([ProviderDimensions.ts#L123-L243](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderDimensions.ts#L123-L243)) |
| `mcp.delegated_task.finished` | [DelegatedTaskAnalytics.ts#L62-L71](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/DelegatedTaskAnalytics.ts#L62-L71) | `status`, caller and target provider and model, `crossProvider`, `completionWake`, `durationSeconds` |
| `client.turn.requested` | [ws.ts#L1486-L1502](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1486-L1502), [#L2294-L2310](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L2294-L2310) | per-socket client props: `surface`, `appVersion`, `clientOs`, `os`, `clientDeviceType`, `webDeployment`, `clientBrowser`, `osMajorVersion`, `deviceModel`, `connectionMethod` ([#L832-L874](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L832-L874)) |
| `client.thread.started` | [ws.ts#L2294-L2301](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L2294-L2301) | client props plus `workspaceStrategy` |
| `feature.used` | [ws.ts#L1493-L1498](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1493-L1498), [#L3827-L3841](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L3827-L3841), plus guest-share calls in `GuestShareService.ts` | `feature`, `variant`, `surface` ([FeatureUsage.ts#L20-L76](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/FeatureUsage.ts#L20-L76)) |
| `install.owner_observed` | [AnalyticsService.ts#L342-L363](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L342-L363) | `ownerSource` (`connect` or `device`), `ownerId`, `observedBy` |
| `server.boot.heartbeat` | [serverRuntimeStartup.ts#L174-L177](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/serverRuntimeStartup.ts#L174-L177) | `threadCount`, `projectCount` |
| `chatgpt.auth.started` / `.completed`, `chatgpt.transfer.started` / `.completed` | [CodexChatGptAuth.ts#L125-L166](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L125-L166), [#L949-L969](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L949-L969), [#L1093-L1095](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L1093-L1095) | `flow`, `intent`, `callbackMode`, `outcome`, `durationMs`, `failureStage`, and counts of connected ChatGPT accounts and connections. The counts are computed locally by de-duplicating emails; the emails are not sent ([#L327-L368](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L327-L368)). [DOC] gap: `telemetry.md` does not mention these events or the account counts. |
| `agent.feedback` (opt-in) | [FeedbackStore.ts#L200-L228](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackStore.ts#L200-L228) | see Part 3.3 |

### 2.5 Defaults and opt-outs by surface [CODE][DOC]

| Surface | Product analytics | Relay traces | Other channels |
|---|---|---|---|
| Server / CLI | **On by default** (`T3CODE_TELEMETRY_ENABLED` defaults to `true`). Off with the env var or a managed policy `telemetry: false` ([AnalyticsService.ts#L125-L149](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L125-L149), [ManagedPolicy.ts#L71-L76](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/policy/ManagedPolicy.ts#L71-L76)). **No in-app toggle.** | On when the build embeds an Axiom config. Off with `T3CODE_TELEMETRY_ENABLED=false`, `T3CODE_OTEL_SDK_DISABLED`, `OTEL_SDK_DISABLED` ([otelEnvironment.ts#L321-L332](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/otelEnvironment.ts#L321-L332), [publicConfig.ts#L86-L102](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/publicConfig.ts#L86-L102)) or by policy ([relayTracing.ts#L17-L36](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/relayTracing.ts#L17-L36)) | Agent-activity publishing, opt-in at host level (Part 3.4) |
| Desktop (Electron) | Same server. On macOS and Linux the opt-out comes from the login shell profile. Analytics wait for shell discovery before sending ([DesktopBackendConfiguration.ts#L577-L584](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/desktop/src/backend/DesktopBackendConfiguration.ts#L577-L584), [DesktopTelemetryReceiver.ts#L244-L275](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/resourceTelemetry/DesktopTelemetryReceiver.ts#L244-L275)). Windows reads User and Machine scope only since `3ba003be`. | See gap G1 below | same |
| Web served by a server | Through the server. No client SDK. | Gated on the server's `relayTracingAllowed` ([web publicConfig.ts#L66-L80](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/cloud/publicConfig.ts#L66-L80), [runtime.ts#L25-L35](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/lib/runtime.ts#L25-L35)) | Device owner hash in `localStorage` |
| Hosted web (`app.t3.codes`) | Through whichever server it connects to | **On by default with no toggle**: `isHostedStaticApp() ? true` ([web publicConfig.ts#L79](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/cloud/publicConfig.ts#L79-L79)). Docs agree ([telemetry.md#L84-L85](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L84-L85)). | |
| Mobile | Through the server | Gated by **Send crash reports** since `dc7b8802` | Crash reports and startup timings **on by default** (`crashReportsEnabled !== false`) ([observe.ts#L46-L66](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/observability/observe.ts#L46-L66)). Server env vars and managed policy do not reach them ([managed-policy.md#L259-L261](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/managed-policy.md#L259-L261)). |
| Managed policy | Can only turn analytics off, never on ([managedPolicy.ts#L81-L82](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/managedPolicy.ts#L81-L82)) | Server, desktop and server-served browser only | |

### 2.6 Concrete bugs and gaps in opt-outs and anonymity

- **G1. Desktop relay tracing may miss a shell-profile opt-out on first launch [CODE, inferred, not runtime-verified; medium-low confidence].**
  - Server relay-broker tracing resolves its config once, at module load, from `process.env` ([relayTracing.ts#L14](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/relayTracing.ts#L14-L14)). `ws.ts` reads `relayTracingAllowed` once, when the layer is built ([ws.ts#L1588-L1591](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1588-L1591)).
  - The desktop starts the backend with `T3CODE_DESKTOP_SHELL_DISCOVERY_PENDING=1` and patches the shell profile's `T3CODE_TELEMETRY_ENABLED` into the environment later ([DesktopTelemetryReceiver.ts#L244](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/resourceTelemetry/DesktopTelemetryReceiver.ts#L244-L244), [#L275](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/resourceTelemetry/DesktopTelemetryReceiver.ts#L275-L275)).
  - `AnalyticsService` explicitly waits for this ([#L128-L149](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L128-L149)). The relay tracer does not.
  - A cached copy of `T3CODE_TELEMETRY_ENABLED` from earlier discovery ([DesktopShellEnvironment.ts#L660-L674](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/desktop/src/shell/DesktopShellEnvironment.ts#L660-L674)) should cover later launches. The window that remains is the first launch after the user sets the opt-out in a shell profile.
- **G2. Agent feedback is anonymous in the payload only [CODE].**
  - The `anonymous` flag swaps `distinct_id` for the event UUID and drops `installId` ([AnalyticsService.ts#L215-L218](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L215-L218)).
  - But `takeBatch` mixes anonymous and identified events in one POST ([#L244-L247](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L244-L247)). Every event also carries host dimensions, including the WSL distro name.
  - So a receiver that keeps batch or request context can re-link reports to the install. The claim that reports "cannot be tied to your installation or to each other" ([telemetry.md#L56-L58](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L56-L58)) is stronger than the code guarantees. Whether the ingest keeps that context is [UNKNOWN].
- **G3. "Anonymous" wording [DOC].** See 2.3. The `connect` hash is unsalted and the same on every surface by design.
- **G4. Free-form strings reach analytics [CODE].** `wsl` and `serverWslDistro` (user-nameable WSL distros); client-supplied `clientAppVersion`, `clientBrowser` and `clientDeviceModel`, bounded by length only; custom model IDs.
- **G5. No in-app control for product analytics or server relay traces [CODE][DOC].** Only an env var or a policy. The privacy policy points users to a shell profile ([privacy-policy.astro#L345-L349](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/marketing/src/pages/privacy-policy.astro#L345-L349)).
- **G6. Historical data [CODE / UNKNOWN].** `84e4264b` and `482e197f` change only future sends. The `openai` and `claude` owner hashes and the legacy provider-derived `distinct_id`s in the dump remain wherever ingest and PostHog stored them. I found no deletion or re-keying code for analytics in this clone. Relay account deletion (`3380585e`) covers relay data only.

## Part 3. Other data T3 Code takes, stores or transmits

### 3.1 Relay connection traces (to Axiom) [CODE]

- **Client and server spans:** these export over OTLP JSON with an `X-Axiom-Dataset` header. The resource carries service name and version, a random per-process `service.instance.id`, runtime, Node and Electron versions, and client surface ([shared relayTracing.ts#L166-L198](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L166-L198), [observability.ts#L36-L56](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/observability.ts#L36-L56)). Since `dc7b8802`:
  - `url.full`, `url.query`, `server.address` and `server.port` are dropped, and so are span events (log lines).
  - Errors keep only type names ([#L72-L140](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L72-L140)).
  - Batches queued before an opt-out are dropped ([#L142-L164](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L142-L164)).
  - Before `dc7b8802`, the server used the operator's own `service.instance.id` if one was set ([relayTracing.ts@11edf884#L28](https://github.com/pingdotgg/t3code/blob/11edf884bc7d8332a69cc2faa563ce91e33bc1da/apps/server/src/cloud/relayTracing.ts#L28-L28)), and the shared tracer exported stack frames ([shared relayTracing.ts@11edf884#L72](https://github.com/pingdotgg/t3code/blob/11edf884bc7d8332a69cc2faa563ce91e33bc1da/packages/shared/src/relayTracing.ts#L72-L72)).
- **Relay-side spans:** now drop the caller's address and user agent, but add Cloudflare `colo`, `country` and `continent` ([Api.ts#L213-L247](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/http/Api.ts#L213-L247)). Before `4eccb0ec` they recorded IP and user agent ([Api.ts@c39c21f8#L234-L243](https://github.com/pingdotgg/t3code/blob/c39c21f870fa75b51c11ef9bec67fcd1a96dc14a/infra/relay/src/http/Api.ts#L234-L243)).
- **Retention:** "configured to expire after 30 days" [DOC] ([privacy-policy.astro#L366-L367](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/marketing/src/pages/privacy-policy.astro#L366-L367)). Actual Axiom retention is [UNKNOWN].

### 3.2 Mobile crash reports and observability [CODE][DOC]

- **Collection:** `expo-observe` installs a global JS error handler. In release builds, every unhandled promise rejection is reported too ([observe.ts#L1-L26](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/observability/observe.ts#L1-L26)).
- **Relay forwarding:** the relay forwards the OTLP payload to Axiom largely as sent, with source-map symbolication. It does not scrub error messages ([MobileTelemetry.ts#L231-L298](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/mobileTelemetry/MobileTelemetry.ts#L231-L298)). The relay reads `cf-connecting-ip` for rate limiting ([#L266-L267](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/mobileTelemetry/MobileTelemetry.ts#L266-L267)). I saw no code that forwards the IP.
- **What the docs say:** reports carry the error message, stack, app version, device model, OS version, and a random install ID, and "an error message can quote a value the app was handling" ([telemetry.md#L87-L99](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L87-L99)).
- **Default:** on.

### 3.3 Agent feedback (local, wire, scrubbing) [CODE][DOC]

- **Mode:** off by default. The modes are Off, When I ask, and Automatic ([telemetry.md#L16-L29](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L16-L29)).
- **Local storage:** the report is saved in SQLite (`agent_feedback`) first.
- **On the wire:** `kind`, `subject`, `trace`, `userRequested`, `source`, and provider and model dimensions. Agent text fields (`expected`, `actual`, `workaround`) go out only when the user approved a card ([FeedbackStore.ts#L205-L220](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackStore.ts#L205-L220)). Automatic reports send `trace: null` ([FeedbackService.ts#L149-L160](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackService.ts#L149-L160)).
- **Scrubbing:** the scrubber redacts token prefixes, JWTs, credential URLs, emails, absolute paths (and the rest of the line), and long high-entropy runs ([scrubFeedback.ts#L7-L36](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/scrubFeedback.ts#L7-L36), [#L79-L124](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/scrubFeedback.ts#L79-L124)). It also redacts these known values: thread and project IDs, home directory, OS username, hostname, worktree path, branch, workspace root, project title, and repository remotes, web URL and owner/name ([FeedbackService.ts#L121-L138](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackService.ts#L121-L138)). It cannot detect code or names written in prose, as the docs say.
- **History:** before `796103f4`, feedback carried the install `distinct_id` and `installId`, and automatic reports also carried the agent text ([AnalyticsService.ts@eb7cc447#L210-L213](https://github.com/pingdotgg/t3code/blob/eb7cc44727335e06cf083b398e73cd4b39b37b68/apps/server/src/telemetry/AnalyticsService.ts#L210-L213), [FeedbackStore.ts@eb7cc447#L206-L210](https://github.com/pingdotgg/t3code/blob/eb7cc44727335e06cf083b398e73cd4b39b37b68/apps/server/src/feedback/FeedbackStore.ts#L206-L210)).
- **Linkage:** see G2.

### 3.4 Agent activity publishing [CODE][DOC]

- **What is sent:** project and thread titles, model names, status, and environment and thread IDs go to the T3 Connect relay for push notifications and Live Activities ([telemetry.md#L101-L110](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/telemetry.md#L101-L110)). Failure details are redacted and the detail length is capped ([AgentAwarenessRelay.ts#L212-L224](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/relay/AgentAwarenessRelay.ts#L212-L224), [#L326-L374](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/relay/AgentAwarenessRelay.ts#L326-L374)).
- **Default:** off on the host unless the stored value is `"true"` ([cloud/config.ts#L43-L45](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/config.ts#L43-L45)). However, **linking an environment from the mobile app sets `publishAgentActivity: true` with no separate prompt in that flow** ([linkEnvironment.ts#L238-L252](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/cloud/linkEnvironment.ts#L238-L252)).
- **Opt-out:** `T3CODE_TELEMETRY_ENABLED` and the managed policy `telemetry` limit do not disable it. The docs acknowledge this.

### 3.5 Local storage [CODE]

Paths are under `<base>/userdata` ([config.ts#L150-L180](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/config.ts#L150-L180)):

- `statev2.sqlite` (threads, turns, projections, feedback)
- `attachments/`, `browser-artifacts/`
- `logs/server.trace.ndjson`
- `logs/provider/events.log`, which holds native and canonical provider events with only streaming deltas excluded. It rotates at 10 MiB × 10 files, with a 512 MiB total cap and 14 days' retention ([EventNdjsonLogger.ts#L28-L41](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/EventNdjsonLogger.ts#L28-L41)). It is always enabled ([server.ts#L271-L290](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/server.ts#L271-L290)).
- `logs/terminals/`
- `anonymous-id`, `environment-id`, `settings.json`
- `secrets/*.bin`, written as raw bytes with directory mode 0700 and file mode 0600 ([ServerSecretStore.ts#L173-L188](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/auth/ServerSecretStore.ts#L173-L188), [#L231-L234](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/auth/ServerSecretStore.ts#L231-L234)). I saw no encryption at rest in this module. I did not check whether other secret providers use an OS keychain.

These files stay local unless a feature above sends something out. I did not open any real instance of these files.

### 3.6 Content sent to configured coding-agent providers [CODE][DOC]

- **Agent sessions:** by design, T3 Code drives provider CLIs and SDKs (Codex, Claude, Antigravity, Cursor, OpenCode and others under `packages/provider-*` and `apps/server/src/provider/Drivers`). Prompts, attachments, repository files that the agents read, and tool output therefore go to whichever provider the user configured, under that provider's terms.
- **Text generation:** thread titles, commit messages, PR text, branch names, and voice cleanup send "what the task needs, such as the staged diff" to the chosen agent or API ([text-generation.md#L31](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/docs/user/text-generation.md#L31-L31)).
- **Retention:** provider-side retention is [UNKNOWN].

## Part 4. Historical changes in the shallow clone (all 2026-11-24)

| Commit | Time (UTC) | Change | Before (parent) |
|---|---|---|---|
| `4eccb0ecfcc12655f3231203f766c56b05692170` | 19:57 | Relay spans drop caller IP and user agent | IP and UA recorded on non-hook relay spans |
| `3380585e1bfcc99634ee78edf02624d396886fd2` | 20:13 | Relay data deleted on Clerk user deletion | none |
| `482e197faeb5dfef69582514bf14769fa019a71a` | 20:19 | Mobile analytics device ID is its own random ID | Hash of the relay agent-awareness device ID, which the relay also stores ([platform.ts@f811978e#L193-L195](https://github.com/pingdotgg/t3code/blob/f811978eefb7cf619307ddebad55b9c5a2beb9bf/apps/mobile/src/connection/platform.ts#L193-L195)) |
| `3ba003be06afbd32a75c69a5cf38fb9719695b70` | 20:24 | Windows reads a saved User or Machine opt-out | Process scope only |
| `84e4264bb347e36e97f6c3bd95d666eecfa12e07` | 20:46 | No provider-account reads; `distinct_id` = install ID | Codex and Claude IDs drove `distinct_id`, `openai` and `claude` owners |
| `796103f4b792847561c65c921e82375a29d016c9` | 20:52 | Feedback sent without install ID; automatic reports drop agent text | Install-linked, with agent text |
| `dc7b8802b84fd658d4be59eec0d3773dfd10aaa2` | 21:12 | Relay tracing honors opt-outs; machine details and stacks removed; mobile traces gated | Operator `service.instance.id`, stack frames, no mobile gate |

- **Overlap with the dump:** the newest dump event is 2026-11-24 17:28 UTC, and the newest nightly build string in the dump is dated 20261122 [DUMP]. **No dump event reflects any of these fixes.**
- **Gap between source and installed builds:** HEAD's server `package.json` says `0.1.11`. I cannot tell from the source which build any user runs.

## Limits

- **Source is not deployment.** I read source at a snapshot. I did not observe live traffic, the ingest service, PostHog, Axiom, the relay deployment, or providers. Ingest IP logging, retention, joins against account data, and what installed builds send are all [UNKNOWN].
- **Shallow clone.** The clone holds 100 commits from one day. I cannot date when `install.owner_observed`, the `connect` owner, or the `device` owner were introduced, except that the first owner events in the dump are from 2026-10-20.
- **One user's data.** The dump is one person's data, already filtered by whoever exported it. Other users' events may differ.
- **G1 is inferred.** It comes from module-load ordering. I did not run the desktop app to confirm it.
- **Nothing executed.** I did not run tests or the report's scripts. My figures come from independent one-liners (below).

## Reproducible read-only commands

```bash
# from the workspace root
git -C t3code-source rev-parse HEAD            # 55085df2a6c384f34b37901d5dcbc5925ada1600
git -C report-repo show b68d58700de22718792327151de0e7ec6b3d8732:ANALYSIS.md | cat -n
git -C report-repo diff --stat b68d58700de22718792327151de0e7ec6b3d8732 HEAD -- results/ data/

# dump integrity
shasum -a 256 report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz
gzip -dc report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz | shasum -a 256
gzip -dc report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz | wc -lc

# owner linkage (installs and distinct_ids per ownerId)
gzip -dc report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz | python3 -c '
import sys,json,collections as co
o=co.defaultdict(lambda:[set(),set(),None])
for l in sys.stdin:
  r=json.loads(l);p=json.loads(r["properties"])
  if r["event"]=="install.owner_observed":
    k=p["ownerId"][:8];o[k][0].add(p["installId"]);o[k][1].add(r["distinct_id"]);o[k][2]=p["ownerSource"]
for k,(i,d,s) in sorted(o.items(),key=lambda x:-len(x[1][0])): print(s,k,len(i),len(d))'

# createdBy / connectionMethod are per event type, not threads or clients
gzip -dc report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz | python3 -c '
import sys,json,collections as co
c=co.Counter();m=co.Counter();u=co.Counter()
for l in sys.stdin:
  r=json.loads(l);p=json.loads(r["properties"])
  if "createdBy" in p: c[(r["event"],p["createdBy"])]+=1
  if "connectionMethod" in p: m[(r["event"],p["connectionMethod"])]+=1
  if r["event"]=="provider.turn.completed": u[p["usageStatus"]]+=1
print(c);print(m);print(u)'

# received_at vs timestamp, inserted_at of pre-Oct-3 rows
gzip -dc report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz | python3 -c '
import sys,json,datetime as dt,collections as co
lag=[];ins=co.Counter()
for l in sys.stdin:
  r=json.loads(l);f=lambda s:dt.datetime.fromisoformat(s[:19])
  lag.append((f(r["received_at"])-f(r["timestamp"])).total_seconds())
  if r["timestamp"]<"2026-10-03": ins[r["inserted_at"][:10]]+=1
lag.sort();print(lag[len(lag)//2],lag[int(len(lag)*.99)],lag[-1],ins)'

# code: analytics callers, identity, owners, relay gates
cd t3code-source
git grep -n "AnalyticsService" -- apps/server/src ":!*.test.ts"
git grep -nE "\.record\(\"|record\(name" -- apps/server/src ":!*.test.ts"
git grep -nE "clientOwner|clientDevice\"" -- apps packages ":!*.test.ts"
git grep -nE "SHELL_DISCOVERY_PENDING|resolveRelayClientTracingConfig\(\)" -- apps ":!*.test.ts"
git grep -n "publishAgentActivity: true" -- apps/mobile/src
git show 84e4264bb347e36e97f6c3bd95d666eecfa12e07 -- apps/server/src/telemetry/Identify.ts
git show "54ba2408f452705a5e43ce3dbdc878b6eeefded4:apps/server/src/telemetry/Identify.ts" | sed -n "18,46p;274,292p;321,338p"
git show 4eccb0ecfcc12655f3231203f766c56b05692170 -- infra/relay/src/http/Api.ts
git show dc7b8802b84fd658d4be59eec0d3773dfd10aaa2 -- packages/shared/src/relayTracing.ts apps/server/src/cloud/relayTracing.ts
git show 796103f4b792847561c65c921e82375a29d016c9 -- apps/server/src/telemetry/AnalyticsService.ts apps/server/src/feedback/FeedbackStore.ts
```
