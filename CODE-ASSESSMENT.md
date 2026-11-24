# T3 Code telemetry and data-handling assessment

The code assessment finds a concrete linkability defect in anonymous feedback, conditional desktop opt-out defects, and several data paths outside product analytics. The published dump is reproducible, but it cannot establish everything T3 Code collects or sends.

The assessments inspect upstream T3 Code at [`55085df2a6c384f34b37901d5dcbc5925ada1600`](https://github.com/pingdotgg/t3code/tree/55085df2a6c384f34b37901d5dcbc5925ada1600). The original report baseline is [`b68d58700de22718792327151de0e7ec6b3d8732`](https://github.com/Ty-Robb/t3-telemetry-report/tree/b68d58700de22718792327151de0e7ec6b3d8732). These are source assessments with offline checks, not audits of an installed application or hosted production traffic.

## Findings that matter

1. **Anonymous feedback can be linked within its HTTP batch.** `FeedbackStore` places feedback in the same queue as identified analytics. The payload serializer removes the feedback event's install ID but can send it beside another event carrying that ID. An offline execution of the actual serializer reproduced this with synthetic events. The ingest receiver can infer the association from that request. Whether it retains or uses the association is unknown. [Source](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L171), [reproduction](results/code-assessment/code-probes.json).
2. **Desktop relay tracing can miss a shell-only opt-out at startup.** Analytics waits for deferred shell discovery, but the server relay tracing module captures configuration at import time without the same pending-discovery check or dynamic send gate. This matters when tracing is configured and the GUI process initially lacks the opt-out. The desktop discovery allowlists also omit both OpenTelemetry SDK disable variables. These are source-supported defects. They have not been reproduced in a running desktop build. Variables already inherited by the process are a different case. [Detailed source trace](reports/antigravity.md#concrete-opt-out-bugs-and-privacy-defects-in-code-at-55085df2).
3. **Product metadata can contain user-chosen text.** Unknown model IDs, model filenames, and the raw WSL distribution name are transmitted. A relative model path such as `models/customer-acme.gguf` survives the filename filter. This makes “only closed enums and hashes” inaccurate as a general privacy guarantee. [Source and executed checks](reports/codex.md#custom-values-leave-through-product-analytics).
4. **The telemetry switch does not cover every data path.** Mobile diagnostics use a separate default-on preference when configured. Activity publishing sends readable project and thread titles when enabled. Relay workers have their own operational tracing. Local messages remain in the application database, and task content goes to the selected agent provider. [Code inventory](reports/antigravity.md#data-outside-product-analytics-code-trace).
5. **Hashes preserve account correlation.** Current analytics identity no longer reads Codex or Claude account IDs. It still hashes T3 Connect account IDs without a salt. A holder of the raw ID can recompute the hash. The published dump contains one Connect owner hash across all 16 install IDs. [Identity implementation](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/Identify.ts#L151), [dump counts](results/code-assessment/corrections.json).
6. **Feedback scrubbing is not a content-safety guarantee.** The actual scrubber removes synthetic email and path examples, but leaves ordinary sensitive prose and a short password example unchanged. This supports retaining the user preview and send boundary. It does not demonstrate an approval bypass. [Executed results](results/code-assessment/code-probes.json).

The immediate engineering priorities are to remove mixed identified/anonymous feedback batches, align relay tracing with deferred shell consent, and forward the SDK disable variables through desktop discovery. Separate batches alone would not guarantee anonymity against a receiver that correlates source IPs or timing. Documentation should state that limit rather than promise that linkage is impossible.

## Provider coverage

These are reports written by agents running through the named providers. They are not official statements from the provider companies.

| Provider | Actual model and account | Report state |
|---|---|---|
| Codex | GPT-6 Astra, medium, `codex` | [Completed code assessment](reports/codex.md). |
| Antigravity | Gemini 4 Neon, `antigravity` | [Completed code assessment](reports/antigravity.md). Codex reviewed the main findings and narrowed unsupported certainty. |
| Grok | Grok 4.7, high, `grok` | Assessment running. |
| Claude | Claude Fable 5.2, high, `claudeAgent_claude_personal` | API rate limit prevented a report. Both the original Claude 03 Opus attempt and the user-selected Claude 02 Fable attempt failed before delivering an assessment. |
| Cursor, OpenCode, fx, Muse Code, Pi | Disabled in the environment | No assessments launched. No opinions have been simulated. |

The environment exposes no fresh per-account quota readings through the available tools. Codex and the failed Claude 03 attempt used starred models. The user explicitly selected Claude 02 Fable for the replacement. Grok and Antigravity had no starred model configured. No account capacity is claimed as verified.

## What was verified

- Both published dump SHA-256 hashes match the original README.
- The original three analysis scripts reproduce all committed results byte for byte.
- Direct dump recounts correct two interpretation errors. The 45,505 events with `createdBy` are turn/request events, not distinct thread creations. Turn-only usage status counts are 1,559 unavailable and 1,418 partial.
- `client.connected` rows with connection methods comprise 4,676 relay, 199 direct, and 2 SSH. The earlier totals combined three event types.
- Offline source probes reproduce the shared feedback envelope, raw WSL value, custom model behavior, and scrubber limitations.

Run the code probes with Node 24 against a checkout of the pinned upstream revision:

```sh
node scripts/code-probes.mjs /path/to/t3code-source
```

The probes import the actual feedback scrubber. They execute the model-label source with an empty catalog to isolate unknown-model behavior and execute the extracted analytics payload expression with synthetic dependencies. They do not run the full analytics service or make network requests. The report includes no real passwords, account credentials, or private conversations.

The original dump commands remain in [README.md](README.md). Additional recount commands are in the [Antigravity report](reports/antigravity.md#reproducible-verification-commands).

## Limits and remaining work

No application dependency installation, full test suite, desktop runtime reproduction, packet capture, customer-data access, or production configuration inspection was performed. The upstream source and report repository remain separate. No upstream code changes or upstream submissions are part of this assessment.

Infrastructure source configures 30-day Axiom retention for relay traces and mobile logs and metrics. Deployed retention, backups, ingest IP logging, historical account-hash deletion, and provider-side retention remain unverified.

Publication is in progress. Grok's report and a fresh review of the final report revision remain outstanding. Claude remains unavailable after both selected accounts returned rate-limit errors. The provider must restore capacity, or the user must select another account, before a Claude report can be produced. Disabled providers require the user to enable them before they can produce their own assessments.
