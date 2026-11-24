# Codex assessment of T3 Code data handling

T3 Code's product analytics is only one of its outbound data paths. The inspected code also implements relay tracing, mobile diagnostics, optional feedback, and optional activity publishing. The code does not support a blanket claim that T3 Code sends only closed enums and hashes, or that its server telemetry setting stops every transmission.

Assessor: OpenAI Codex, GPT-6 Astra, medium reasoning, provider instance `codex`. Date: 24 November 2026. This is an independent source assessment, not an official OpenAI privacy statement.

Inspected T3 Code revision: `55085df2a6c384f34b37901d5dcbc5925ada1600`. Report repository baseline: `b68d58700de22718792327151de0e7ec6b3d8732`. No installed application settings, user conversations, customer records, provider credentials, or production traffic were inspected for this assessment. Upstream source is not proof of the installed or deployed revision.

## Findings

### Custom values leave through product analytics

`AnalyticsService` enables telemetry by default, uses `https://ingest.t3.codes/batch/`, and appends the unmodified `WSL_DISTRO_NAME` as both `wsl` and `serverWslDistro`. A user-chosen distribution name can identify a project or organization. This is a concrete collection behavior, not evidence that the published dump contains such a name.

`modelLabel` strips directories from absolute, home-prefixed, dot-relative, and Windows paths, but deliberately retains unknown model identifiers. It also retains a slash-separated relative model path such as `models/customer-acme.gguf`. Even a recognized absolute file path becomes a potentially identifying filename such as `customer-acme.gguf`. A model identifier and a local filename are therefore not guaranteed to be anonymous.

Sources: [analytics defaults](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L71), [payload construction](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L209), [model normalization](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderDimensions.ts#L29), and [provider event emission](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L406).

Assessment: a privacy limitation and a relative-path normalization gap. Preserve custom model reporting only if this disclosure is intentional. If the intended guarantee is that paths never leave, unknown identifiers need a stricter reporting policy. Slash-separated provider model IDs mean blindly removing every slash is not a complete design.

### Mobile diagnostics are a separate default-on collection path

When a relay is configured, an absent crash-report preference resolves to enabled through `preferences.crashReportsEnabled !== false`. Production unhandled promise rejections go to `Observe.reportError`. The relay accepts mobile telemetry bodies, optionally symbolicates logs, and forwards them to Axiom. On symbolication failure it forwards the original body. This forwarding path does not apply the feedback text scrubber.

Consequently, an error message containing sensitive text can leave in diagnostics. The server's `T3CODE_TELEMETRY_ENABLED=false` does not control this mobile preference. The relay also reads `cf-connecting-ip` for rate limiting. That proves IP processing on this route, not permanent IP storage or IP logging at the separate product ingest endpoint.

Sources: [mobile enablement and error hook](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/observability/observe.ts#L19), [mobile trace gate](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/observability/tracing.ts#L35), [IP processing and forwarding](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/mobileTelemetry/MobileTelemetry.ts#L275).

Assessment: default-on error collection deserves separate disclosure. A clean product-event dump cannot establish that crash diagnostics contain no personal information.

### Feedback redaction is useful but cannot establish content safety

Agent feedback defaults to off. Requested reports can include agent-written text and an explicitly approved conversation excerpt. `FeedbackStore.deliver` uses a fresh anonymous event identity and excludes the install ID. Automatic reports omit the agent-written description fields.

I ran the actual dependency-free `scrubFeedback` implementation with synthetic text. It redacted an email and a home-directory path. It left both `Patient Alice has diabetes` and `password=hunter2` unchanged when no caller-specific sensitive values were supplied. These are synthetic examples, not discovered user data. They prove that the scrubber is a pattern filter, not a general sensitive-content detector. They do not prove an approval bypass.

Sources: [default off](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/settings.ts#L1408), [scrubber](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/scrubFeedback.ts#L86), [delivery fields](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackStore.ts#L200), and [anonymous event construction](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L216).

Assessment: retain the preview and explicit-send boundary. Do not describe scrubbing as a guarantee that secrets or personal information cannot be sent.

### Activity publishing sends readable titles independently of analytics

`projectThreadAwarenessV2` includes project title, thread title, model name, environment ID, thread ID, status, timestamp, and a deep link. The relay publisher reads its own saved preference and sends this state. Its sanitization replaces failure detail but preserves titles. The publishing preference is enabled only when its saved value is exactly `true`.

Sources: [state fields](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/agentAwareness.ts#L134), [title-preserving sanitization](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/relay/AgentAwarenessRelay.ts#L212), [publishing gate and request](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/relay/AgentAwarenessRelay.ts#L506), [default-disabled interpretation](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/config.ts#L43).

Assessment: intentional feature data, outside product analytics. Disable Publish agent activity separately if titles must not go to the relay.

## Other code-confirmed handling

- Product analytics uses a persistent random install ID hashed with SHA-256. Owner observations can link installs through hashed T3 Connect account IDs and client device IDs. The current `Identify.ts` no longer derives analytics identity from Codex or Claude sign-in files. Hashing still permits correlation. [Identity implementation](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/Identify.ts#L114).
- The analytics service accepts arbitrary property records and spreads them into the outbound payload. It has no central property allowlist or content scrubber. This places the privacy boundary at each event producer. Type System Discipline shaped this assessment: the open record type provides less structural protection than a closed event schema. This is a maintenance risk, not proof that ordinary prompts currently enter analytics. [Service contract](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L84).
- Server relay tracing respects environment opt-outs and managed telemetry policy. Its tracer removes full URLs, query strings, server addresses, ports, raw span log events, and error messages and stacks. It retains other attributes and error types. This is a denylist, not proof every possible attribute is harmless. [Configuration gate](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/publicConfig.ts#L86), [managed policy](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/relayTracing.ts#L22), [trace filter](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L81).
- Hosted relay code has its own observability. Account deletion annotates a span with the raw relay user ID. Infrastructure declares 30-day retention for relay traces, mobile logs, and mobile metrics. These are source-defined settings, not a verified production retention guarantee. [Account annotation](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/accounts/AccountDeletion.ts#L106), [dataset configuration](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/observability.ts#L31).
- T3 Code stores message payloads and searchable message text in its local SQL projections. Disabling analytics does not disable the application database. [Message persistence](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/orchestration-v2/ProjectionStore.ts#L3080).
- Provider requests carry task input and context separately from analytics. The inspected Codex adapter constructs a request containing input, additional application and workspace context, working directory, model, and runtime policy. This establishes what T3 passes to the provider adapter, not the provider's retention or training practices. [Codex request construction](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/orchestration-v2/Adapters/CodexAdapterV2.ts#L974).

## Verification and limits

The published compressed and uncompressed SHA-256 hashes match the README. All three scripts ran successfully against the decompressed dump. `profile.txt`, `analysis.json`, and `extras.json` matched the committed results byte for byte. Reproducibility does not validate every interpretation: the PII scan examines top-level property strings and `user_agent` with a limited regex set, not all possible sensitive information.

The feedback checks executed the actual source file under Node 24.18.0. The model-label checks executed the TypeScript-stripped source with imports removed and an empty bundled model manifest, isolating unknown-model behavior. They returned `customer-acme.gguf`, `models/customer-acme.gguf`, and `acme-private-model` for the corresponding synthetic inputs. This was not an end-to-end network test.

No dependencies were installed and no full application suite was run. No production receiver, account logs, installed application, or packet capture was inspected. Product ingest retention, historical hash deletion, actual deployment configuration, and provider-side handling remain unverified. The published dump cannot settle those questions.

## Repository assessment

The repository is reproducible and useful as an analysis of one published product-event export. Its privacy language is stronger than its scanner establishes. Narrow the absence claim to the inspected file and patterns. Add these separately sourced code paths and retain a clear distinction between historical behavior, the pinned current source, and observed production traffic. No evidence here supports calling this a complete audit of every T3 Code data flow.
