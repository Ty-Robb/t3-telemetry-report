# T3 Code collection, storage, and transmission

## Review note

Grok 4.7 authored this assessment independently. Antigravity verified all 70 source permalinks against the pinned checkout and parent commit, corrected one off-by-one end line (`Identify.ts#L103-L164`), and corrected the `runtime.test.ts` stub description (`T3CODE_TELEMETRY_ENABLED` is stubbed `"false"`, while `T3CODE_OTEL_SDK_DISABLED` and `OTEL_SDK_DISABLED` are stubbed `"true"`). The local scratch checkout path in the method table was shortened to `t3code-source`.

Cross-check notes against `55085df2` and the report repository:
- Although the prompt and method table cite baseline `b68d587`, Grok inspected `ANALYSIS.md` after commit `8fc2ef0` and before the follow-up revision that incorporated Grok's owner-hash split and `dc7b880` notes.
- In [`apps/web/src/cloud/publicConfig.ts#L76-L79`](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/cloud/publicConfig.ts#L76-L79) and [`apps/web/src/appInit.tsx#L281`](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/appInit.tsx#L281), hosted web defaults relay tracing on while disconnected or before a server answers (`serverRelayTelemetry ?? (isHostedStaticApp() ? true : null)`); once connected to a server reporting `relayTracingAllowed: false`, `setServerRelayTelemetry(false)` overrides the hosted default. On desktop, `??=` caches the first non-null boolean rather than `null`.
- In [`packages/contracts/src/orchestratorMcp.ts#L581`](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/orchestratorMcp.ts#L581), `OrchestratorMcpThreadSendResult.delivery` is server-produced and schema-constrained to `Schema.Literals(["started", "queued", "steered", "restarted"])`, resolving Hypothesis #5 below.
- `scripts/analyse.py` is Python (`isinstance(v, str)`, not `typeof`), with the same non-recursive top-level scan limitation noted below.

Grok 4.7 (`grok-4.7`), through the Grok harness, assessed the T3 Code source at `55085df2a6c384f34b37901d5dcbc5925ada1600`. This is a read of the implementation. It is not a packet capture, not a read of a live database, and not a re-count of the published event dump.

At this snapshot the server queues product events and POSTs them to `https://ingest.t3.codes/batch/` by default, with a compiled-in `phc_` write key. Product telemetry is on unless `T3CODE_TELEMETRY_ENABLED` is false, a managed policy denies `telemetry`, or desktop shell discovery has not finished. The current identity is an unsalted SHA-256 of a random install id. The same process still sends the raw `WSL_DISTRO_NAME`, a length-capped mobile device model, a length-capped web browser string, and any custom model id that is not shaped like a file path.

Five commits on 24 Nov 2026, all ancestors of this snapshot, removed stronger behavior that older builds still have. Before `84e4264` the server read `~/.codex/auth.json` and `~/.claude.json` and hashed provider account ids into `distinct_id` and `install.owner_observed`. Before `482e197` the mobile analytics device id was the relay device id. Before `3ba003be` the Windows desktop app did not apply a saved user opt-out. Before `796103f` agent feedback was sent with the install id. Before `dc7b880` relay traces could carry machine details that the current exporter strips.

Other channels do not share that opt-out. Hosted web relay traces default on and ignore `T3CODE_TELEMETRY_ENABLED`. Mobile crash reports default on and the relay forwards the Observe body, including exception text. Agent-activity publishing is off until a local secret is the string `true`, and when it is on it sends project titles, thread titles, and the raw model id to the relay. Conversation text stays in local SQLite. This pass did not trace the bytes a model provider receives.

The ingest server, PostHog project settings, Axiom retention, and the deployed worker are not in this checkout. Nothing below claims what those hosts log.

## Method and pins

| Item | Value |
|---|---|
| Assessor | Grok 4.7, model id `grok-4.7`, Grok harness in T3 Code |
| T3 source | `t3code-source` (pinned checkout of `pingdotgg/t3code`) |
| Source SHA | `55085df2a6c384f34b37901d5dcbc5925ada1600` (2026-11-24 13:21:01 -0800) |
| Report repo SHA | `b68d58700de22718792327151de0e7ec6b3d8732` |
| Dump gzip sha256 | `6388379c1c9ea2f814b38960156a51531df7c9db70cf9b511e96bc6b2fd0b39a` |
| History | `git rev-parse --is-shallow-repository` is `true`. `git rev-list --count HEAD` is 100 |

Permalinks use `https://github.com/pingdotgg/t3code/blob/<full sha>/<path>#Lstart-Lend`. Line numbers are from the files read in this checkout.

Three labels are used on purpose.

- Proven means the cited function, test, or diff does the thing.
- Historical means the parent of a commit that is an ancestor of HEAD does the thing, and HEAD no longer does.
- Hypothesis means the code leaves the behavior open, or the host that would decide it is absent from this repo.

`ANALYSIS.md` figures are that document's measurements. This assessor did not re-parse the jsonl.

This checkout is not the running installed app. A build from before the commits below still does what those parents do.

## Product analytics

### What leaves the machine

`AnalyticsService.sendBatch` builds a JSON body and POSTs it to `${posthogHost}/batch/`. The default host is `https://ingest.t3.codes`. The default key is `T3CODE_POSTHOG_KEY`, and the source compiles in a `phc_` write key when the variable is unset. The body fields are `api_key`, and a `batch` of `uuid`, `event`, `distinct_id`, `properties`, and `timestamp`. The timestamp is the capture time in ISO form. The uuid is a UUIDv7 from the enqueue path.

Source: [AnalyticsService.ts lines 69-82 and 205-241](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L69-L241).

The first comment in that file says T3 ingest keeps events and forwards them to PostHog. That is a comment in the client. The ingest implementation is not in this repository. Whether ingest stores the client IP, the HTTP User-Agent, or a copy beyond the JSON body is unknown hosted behavior. The client JSON does not contain an IP or a User-Agent field. If the published dump has `user_agent`, something after this client added it.

Every item sets `$process_person_profile` to `false`. That is a field in the JSON the client sends. Whether the receiver honors it is unknown hosted behavior.

Flush runs every 10 seconds. A send times out after 10 seconds. Shutdown waits 1 second and then drops what is still queued. A failed batch retries until it has been failing for 30 minutes. The buffer holds 1,000 events and drops the oldest past that. Batch size defaults to 20. Statuses 400, 401, and 413 are defined as rejections that retrying cannot fix. Each observer keeps at most 1,000 owner ids per process.

Source: [AnalyticsService.ts lines 44-61 and 171-203](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L44-L203).

A null `distinctId` makes `sendBatch` return before the POST. Identity failure therefore disables product telemetry.

### Identity at this snapshot

`hashTelemetryId` is unsalted SHA-256, hex-encoded with `@noble/hashes/sha2`. `isTelemetryIdHash` accepts only 64 lowercase hex characters. Anyone who has the raw id can recompute the hash. The hash is not reversible by guessing a high-entropy id.

Source: [telemetryId.ts lines 5-12](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/telemetryId.ts#L5-L12).

`getTelemetryIdentity` reads or creates a UUIDv4 at `anonymousIdPath`, which `deriveServerPaths` places at `<stateDir>/anonymous-id`. `stateDir` is `<baseDir>/userdata`, or `<baseDir>/dev` for a dev URL. `distinctId` and `installId` are the same hash of that file. The comment on the function says identity does not come from a provider sign-in file. A read or write failure logs a warning and returns null, which disables sending.

Source: [Identify.ts lines 103-164](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/Identify.ts#L103-L164) and [config.ts lines 144-180](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/config.ts#L144-L180).

Owners at HEAD are only `connect` and `device`. The server owner is the hash of the linked T3 Connect user id in the secret `CLOUD_LINKED_USER_ID`, when that secret is non-empty. Clients may also report `connect` and `device`, and the server accepts the value only when it already matches `isTelemetryIdHash`.

`readClientOwnerParams` hashes the Clerk or Connect account id and the analytics device id before they are placed on the websocket query string. The comment says only hashes leave the client.

Source: [remote.ts lines 45-62 and 108-113](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/authorization/remote.ts#L45-L113) and [ws.ts lines 876-896](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L876-L896).

`recordOwners` emits `install.owner_observed` with `ownerSource`, `ownerId`, and `observedBy` (`server` or `client`), once per owner per process. Boot calls it with the server owners.

Source: [AnalyticsService.ts lines 342-360](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L342-L360) and [serverRuntimeStartup.ts lines 174-178](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/serverRuntimeStartup.ts#L174-L178).

Anonymous events, used by agent feedback, set `distinct_id` to the event uuid and omit `installId`.

### Identity before 84e4264

Parent `54ba2408f452705a5e43ce3dbdc878b6eeefded4` is in this shallow checkout. Commit `84e4264bb347e36e97f6c3bd95d666eecfa12e07` (2026-11-24 12:46:02 -0800, "analytics no longer reads or sends Codex and Claude account IDs") is an ancestor of HEAD and removes that reader. HEAD's `CodexChatGptAuth.ts` has no `recordOwners` call.

The parent is proven historical behavior, not current behavior.

`TelemetryOwnerSource` was `connect | openai | claude | device`. `readProviderLogins` read `~/.codex/auth.json` and `~/.claude.json`.

`distinct_id` priority was the hash of Codex `tokens.account_id`, else the hash of Claude `userID`, else the anonymous install hash. `installId` stayed the anonymous hash. The comment on `getTelemetryIdentityForHome` says this `distinct_id` can change on login or be shared by a Codex Team.

The Codex schema comment says `account_id` is the ChatGPT workspace, which a whole Team shares, and the `id_token` names the person. The OpenAI owner id was `user_id` from that token. `openAiUserId` base64url-decodes the JWT payload without verifying it and reads `user_id` from the claim `https://api.openai.com/auth`. The comment says `user_id` is the OpenAI account and is the same for every login, while `sub` names the login method. The Claude owner was `oauthAccount.accountUuid`. Claude `userID` was only the `distinct_id` fallback, and the schema comment says `userID` is random per machine.

Source, parent SHA: [Identify.ts lines 18-47, 177-189, 253-341](https://github.com/pingdotgg/t3code/blob/54ba2408f452705a5e43ce3dbdc878b6eeefded4/apps/server/src/telemetry/Identify.ts#L18-L341).

Consequences that follow from that code:

- `install.owner_observed` with `ownerSource: openai` is the unsalted hash of the OpenAI `user_id` inside the id token, when the token was present and decoded.
- The legacy `distinct_id`, when Codex ChatGPT tokens existed, is the unsalted hash of `account_id`. That value can be shared by a ChatGPT Team. The parent comment states the team share. The dump was not used to prove that a particular hash is a team hash.
- `ownerSource: claude` is the hash of `accountUuid`. It is a different input from the Claude `userID` used as `distinct_id`.
- The commit does not delete events already stored. Deletion or re-keying is unknown hosted behavior.

`ANALYSIS.md` still describes these as "SHA-256 of the OpenAI user_id / Codex account_id or Claude IDs". That sentence merges two different inputs. The owner event and the legacy `distinct_id` are not the same hash.

### Properties attached to every product event

`sendBatch` spreads the event properties and then adds:

- `installId`, omitted when identity is null or the event is anonymous
- `$process_person_profile: false`
- `platform` and `arch` from the host process
- `wsl` and `serverWslDistro`, both the raw `WSL_DISTRO_NAME` when that variable is set
- `t3CodeVersion` and `serverAppVersion` from the server `package.json`
- `telemetryChannel`
- `clientType`, `desktop-app` when `serverConfig.mode === "desktop"`, otherwise `cli-web-client`
- `serverOs`, mapped from the Node platform to `macOS`, `Windows`, `Linux`, `Android`, or `other`
- `serverMode`

`WSL_DISTRO_NAME` is a user-chosen string. It is not hashed and it is not checked against an enum. It is also used locally to pick a file manager and to qualify the environment label. Those local uses do not send it. The analytics copy does.

Source: [AnalyticsService.ts lines 216-231](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L216-L231).

### Properties copied from the connecting client

`readClientAnalyticsProps` copies websocket query parameters onto later analytics calls for that socket.

A predicate or a parsed integer accepts `clientSurface`, `clientOs`, `clientDeviceType`, `clientWebDeployment`, `connectionMethod`, and mobile `osMajorVersion` when it is a positive integer. Mobile `os` is copied again only for `iOS` or `Android`.

Length-capped free strings:

- `clientAppVersion`, trimmed, at most 64 characters, stored as both `appVersion` and `clientAppVersion`
- `clientBrowser` for `surface=web`, trimmed, at most 64 characters
- `clientDeviceModel` for `surface=mobile`, trimmed, at most 80 characters, stored as both `deviceModel` and `clientDeviceModel`

Source: [ws.ts lines 809-873](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L809-L873).

The mobile app sets `deviceModel` from `expo-device` `Device.modelName`. Its session label is the constant `T3 Code Mobile`. That label is presentation metadata. `readClientAnalyticsProps` does not copy a client label, so the constant label is not a product-analytics property. The device model is.

Source: [authClientMetadata.ts lines 5-23](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/lib/authClientMetadata.ts#L5-L23) and [remote.ts lines 97-103](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/authorization/remote.ts#L97-L103).

A client-runtime test builds a mobile URL whose model is `Pixel 9` and whose OS major version is 15. That shows the query-string shape. It is not a capture of production traffic.

Mobile keeps two random UUIDs. `t3code.agent-awareness.device-id` is the relay device id. `t3code.analytics.device-id` is the analytics id. The analytics capability loads the second key. The hash of that id is what `clientDevice` carries.

Source: [mobile-storage.ts lines 11-12 and 192-194](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/persistence/mobile-storage.ts#L11-L194) and [platform.ts lines 193-213](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/connection/platform.ts#L193-L213).

Before `482e197faeb5dfef69582514bf14769fa019a71a` (2026-11-24 12:19:23 -0800), `ClientCapabilities.AnalyticsDevice.id` was `loadOrCreateAgentAwarenessDeviceId`. The comment removed by that commit said the relay device id already persisted and analytics only sent its hash. HEAD separates the keys. Hashes already sent are not deleted by the commit.

The web client stores its analytics device id under `t3code:analytics-device-id` in [apps/web/src/connection/platform.ts](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/connection/platform.ts#L351). This pass did not trace that web storage implementation past the key name.

### Events the current server records

`git grep` for `analytics.record(` in application code, excluding tests, finds these product events. The string `client.connected` does not occur in `*.ts`, `*.tsx`, or `*.md` in this snapshot. The shallow history cannot show an emitter older than these 100 commits. `ANALYSIS.md` counts `client.connected` in the dump. That count was not recomputed here. The emitter of those dump rows is unknown from this checkout.

| Event | What the recorder puts in properties | Source |
|---|---|---|
| `server.boot.heartbeat` | `threadCount`, `projectCount` | [serverRuntimeStartup.ts lines 174-177](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/serverRuntimeStartup.ts#L174-L177) |
| `install.owner_observed` | `ownerSource`, `ownerId`, `observedBy` | [AnalyticsService.ts lines 357](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L357) |
| `client.turn.requested` | origin properties at the dispatch sites in `ws.ts` | [ws.ts lines 1491 and 2306](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1491) |
| `client.thread.started` | properties at the launch site | [ws.ts line 2298](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L2298) |
| `feature.used` | `feature`, and sometimes `variant` | [FeatureUsage.ts](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/FeatureUsage.ts#L20-L76), [ws.ts lines 1495 and 3834](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1495), [GuestShareService.ts lines 390 and 487](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/guest/GuestShareService.ts#L390) |
| `provider.turn.completed` | driver, terminal status, token counters, closed effort and service tier, runtime and interaction mode, origin, segment, child kind, duration, observed model | [ProviderUsageAnalytics.ts lines 174-204 and 412-417](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L174-L204) |
| `provider.request.completed` | report version 2, summed tokens, lifecycle flag, mixed or observed model, duration | [ProviderUsageAnalytics.ts lines 333-370 and 419-423](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L333-L423) |
| `mcp.delegated_task.finished` | status, caller and target provider and model, `crossProvider`, `completionWake`, `durationSeconds` | [DelegatedTaskAnalytics.ts lines 62-71](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/DelegatedTaskAnalytics.ts#L62-L71) |
| `mcp.tool.invoked` | tool name, caller provider and model, origin, depth capped at 5, duration, outcome, error code, and for handoffs the settings below | [McpHttpServer.ts lines 1131-1188](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/mcp/McpHttpServer.ts#L1131-L1188) |
| `chatgpt.auth.started` and `chatgpt.auth.completed` | `flow` (`direct` or `primary_handoff`), `intent` (`saved_profile`, `different_account`, or `default`), `callbackMode` (`server` or the caller value), plus on completion `outcome`, `durationMs`, optional `failureStage`, and account counts | [CodexChatGptAuth.ts lines 125-166 and 949-969](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L125-L166) |
| `chatgpt.transfer.started` and `chatgpt.transfer.completed` | `flow: primary_handoff`, plus the same completion fields | [CodexChatGptAuth.ts lines 1092-1099](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L1092-L1099) |
| `agent.feedback` | anonymous. See the feedback section | [FeedbackStore.ts lines 200-220](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackStore.ts#L200-L220) |

`accountCounts` puts local ChatGPT emails into a `Set` and returns `accountCountScope`, `connectedAccountCount`, `connectedConnectionCount`, `savedConnectionCount`, and `unidentifiedConnectedConnectionCount`. The comment says email is for local counting and is never exported. The method list shown in the product can include `accountEmail`. That list is not the object passed to `track`.

Source: [CodexChatGptAuth.ts lines 327-368 and 937-946](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/CodexChatGptAuth.ts#L327-L368).

`providerDimensions` reports `provider.driver`, not the user-defined instance id. `modelLabel` maps a catalog slug, alias, or dated snapshot to the catalog slug. A string matching `FILE_PATH` is reduced to its final path segment. `FILE_PATH` matches a leading `/`, `~`, `./`, `../`, a Windows drive, or any backslash. Any other id is sent unchanged. A URL such as `https://internal.example/model` does not match, because it does not start with those path forms and contains no backslash. The basename of a real path can still name a private model file.

Source: [ProviderDimensions.ts lines 14-49](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderDimensions.ts#L14-L49).

Effort is reported only when it is in the closed set `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, `ultrathink`, `ultracode`, `brutal`. Service tier is mapped through a closed map (`default` to `standard`, `flex`, `fast`, `priority` to `fast`, `ultrafast`). A Claude `fastMode` boolean becomes `fast` or `standard`. Other effort or tier strings are omitted.

Source: [ProviderUsageAnalytics.ts lines 90-126 and 144-156](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderUsageAnalytics.ts#L90-L156).

`mcp.tool.invoked` is recorded from T3's own MCP server wrapper. Successful calls are skipped unless the tool is a handoff. Failures are recorded. This does not observe third-party MCP tools that a provider harness calls on some other server.

`handoffSettings` documents closed enums and booleans, and most arms use `oneOf` against a literal list. `delegate_task` mode is `async` or `wait`. `t3_thread_launch` workspace type is `scratch`, `root`, `worktree`, or `existing_worktree`. `create_threads` reports `batchSize` and `targetChosen`. `schedule_task` reports `bindToCurrentThread` when the saved id is a string or null. `t3_thread_send` copies `output.delivery` with `stringField` and no allow-list. That one arm does not enforce the comment's closed-enum claim. Prompts, titles, and ids are not read by the arms that were inspected.

Source: [ProviderDimensions.ts lines 118-167](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/ProviderDimensions.ts#L118-L167).

`feature.used` variants for the editor, git stacked action, and pull-request action are copied by `literal`, which only checks that the field is a string. The RPC payloads that feed those methods are closed before that copy. `EditorId` is `Schema.Literals` of the editor catalog. `GitStackedAction` is `commit`, `push`, `create_pr`, `commit_push`, `commit_push_pr`. `PullRequestAction` is `merge`, `ready`, `draft`, `close`, `reopen`, `delete-branch`, `update-branch`, `enable-auto-merge`, `disable-auto-merge`, `revert`, `approve-workflows`. A caller that reached `featureUsage` without that RPC decode could put any string in `variant`. The websocket RPCs decode those payloads first.

Source: [FeatureUsage.ts lines 51-66](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/FeatureUsage.ts#L51-L66), [editor.ts line 151](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/editor.ts#L151), [git.ts lines 19-25](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/git.ts#L19-L25), [pullRequest.ts lines 67-79](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/pullRequest.ts#L67-L79).

Command features copy `runtimeMode` and `interactionMode` off the decoded command. This pass did not re-read those command schemas. Guest-share features recorded directly are `guest_share.join` and the feature at `GuestShareService.ts` line 487.

### Opt-out for product events

`T3CODE_TELEMETRY_ENABLED` defaults to true through `Config.withDefault(true)`.

A managed policy can only turn analytics off. `deniedBy(..., "telemetry")` is consulted at construction, and the comment says a policy never turns analytics on.

While `T3CODE_DESKTOP_SHELL_DISCOVERY_PENDING` is `1`, `record` returns false and does not enqueue, even if the process started with telemetry enabled. The startup value of that flag is captured once. After the flag is no longer `1`, a process that started in the pending state rereads `T3CODE_TELEMETRY_ENABLED` from the discovered environment. A missing name defaults to true. A value that does not parse defaults to false. The unit test file `AnalyticsService.test.ts` records `test.before-discovery`, `test.opted-out`, and `test.allowed` against that sequence. This pass did not re-run the test.

Source: [AnalyticsService.ts lines 126-149](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/telemetry/AnalyticsService.ts#L126-L149).

macOS and Linux desktop discovery copies `T3CODE_TELEMETRY_ENABLED` from the login shell. The name is in `LOGIN_SHELL_ENV_NAMES`.

On Windows, `WINDOWS_PROFILE_ENV_NAMES` now includes `T3CODE_TELEMETRY_ENABLED`, and the desktop shell copies it onto the server environment when the process does not already have it. `windowsEnvironmentValueCommand` reads Process, then User, then Machine, and keeps the first non-empty value.

Before `3ba003be06afbd32a75c69a5cf38fb9719695b70` (2026-11-24 12:24:10 -0800, "Windows desktop applies the saved user telemetry opt-out"), `WINDOWS_PROFILE_ENV_NAMES` was only `PATH`, `FNM_DIR`, and `FNM_MULTISHELL_PATH`. The PowerShell command was `[Environment]::GetEnvironmentVariable('<name>')`, which reads the process scope. A User or Machine variable set after the process started was invisible, and the profile capture did not ask for the telemetry name. That is a proven same-day bug in the parent. HEAD contains the fix. An older Windows desktop build can still ignore a saved user opt-out.

The dev runner sets `T3CODE_TELEMETRY_ENABLED` to the base environment value or `"false"`. Desktop and CLI smoke scripts in `scripts/` set it to `"false"`. Those defaults cover the development and smoke processes that contain those assignments. They do not change a packaged app.

No in-app product-telemetry toggle was traced in this pass. Settings OpenTelemetry export and resource-telemetry diagnostics are the operator's own receiver. They are a different path from the product POST, and they are described with local storage below. Mobile crash reports have their own preference. Agent feedback has a separate off mode that raises `FeedbackOffError`.

## Relay traces

Relay client traces are OTLP JSON to an Axiom dataset. The exporter sets `Authorization: Bearer <token>` and `X-Axiom-Dataset`. Resource attributes are service name and version, namespace `t3code`, a `service.instance.id`, runtime, component, and client surface, plus any attributes the caller passes.

The server relay layer calls `processServiceInstanceId()` with no operator attributes, so the id is a `crypto.randomUUID()` cached for the process. The operator's `service.instance.id` is not copied. The layer also installs `ConfigProvider.fromEnvRecord({})`, so `OTEL_RESOURCE_ATTRIBUTES` from the process are not applied to this exporter. The operator OTLP resource is a different function and does include `host.name`. That split is proven by the two builders, and by the relay test below.

Source: [relayTracing.ts lines 166-198](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L166-L198), [apps/server/src/cloud/relayTracing.ts lines 16-36](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/relayTracing.ts#L16-L36), [observability.ts lines 36-56](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/observability.ts#L36-L56), [config.ts lines 125-140](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/config.ts#L125-L140).

`nonInterferingTracer` replaces the span `attribute` method so later writes of `url.full`, `url.query`, `server.address`, and `server.port` are dropped. It replaces `event` with a no-op, so Effect log events are not exported. `traceSafeError` replaces a failure with an `Error` whose message and stack are the error name, and walks `cause` the same way.

The wrapper calls `delegate.span(options)` before it replaces `attribute`. Attributes already inside the options object are therefore not filtered by that method patch. The flush test still creates a span with `Effect.withSpan` options that set `url.full` to `http://studio-mac.local:3773/api/threads?cursor=secret`, plus `url.path`, `url.query`, `server.address`, and `server.port`. The exported body contains `/api/threads`. It does not match `studio-mac`, `cursor=secret`, `server.port`, `private error detail`, or `private-host`. The test also sets `OTEL_RESOURCE_ATTRIBUTES` to `host.name=private-host` and expects that value to be absent. A separate test fails a span whose message and stack contain `studio-mac` and `/home/user/private.mjs`, and expects the exported error text to contain neither.

The composed exporter in that test keeps `url.path`. It drops those address and query keys when they are set the way the test sets them, drops the log line, drops the error message and stack, and does not export that resource host name. `url.path` can still be identifying if a route embeds an id. The path in the test is `/api/threads`.

Source: [relayTracing.ts lines 72-139](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.ts#L72-L139) and [relayTracing.test.ts lines 70-141](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/relayTracing.test.ts#L70-L141).

`dc7b8802b84fd658d4be59eec0d3773dfd10aaa2` (2026-11-24 13:12:51 -0800, "respect relay tracing opt-outs and remove machine details") is an ancestor of HEAD. Current `docs/user/telemetry.md` lines 68-71 say traces carry timings, request paths, environment and thread identifiers, and error types, and omit machine addresses, query strings, log lines, error messages, and stack frames. That sentence matches the current exporter test. `ANALYSIS.md` still says the project's docs say traces can include the connected machine's name. That sentence matches the docs at the older revision `ANALYSIS.md` cites (`11edf884`), from earlier the same day. It does not match `telemetry.md` at this SHA. Older installed builds can still export the pre-`dc7b880` payload. This pass did not re-read the full `dc7b880` diff for `apps/mobile/src/features/observability/tracing.ts`.

When the relay layer is given `isEnabled`, a span started while the callback is false uses the native tracer, and a batch whose callback is false at flush is replaced with an empty 202 response. An opt-out therefore drops a batch that was queued earlier, for layers that pass `isEnabled`.

### What a connection span contains

`relay.connection.attempt` is created with `root: true` inside `withRelayClientTracing`. Its attributes are `environment.id`, `environment.target.kind`, attempt, generation, and retry failure count, then outcome, route, failure tag, and failure reason. The attempt span does not set `environment.label`.

`annotateTarget` does set `environment.label` on the current span, and `EnvironmentSupervisor.make` calls it at the start of setup. That call is outside the attempt span. Whether `make` runs under an already exported relay parent was not established. The attempt span is a root span, which limits what it inherits. A label leak through some other current span remains a hypothesis.

Source: [supervisor.ts lines 179-185, 277-298, and 553-595](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/client-runtime/src/connection/supervisor.ts#L179-L595).

`environment.id` on that span is an identifier sent to the relay trace dataset. The local environment label, by contrast, prefers `T3CODE_ENVIRONMENT_LABEL`, then a friendly host label, then the hostname. On WSL the hostname form is `<hostname> WSL (<distro>)` when `WSL_DISTRO_NAME` is set. That label is local connection metadata. It is not a field in `sendBatch`.

Source: [ServerEnvironmentLabel.ts lines 196-225](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/environment/ServerEnvironmentLabel.ts#L196-L225).

### Who may send relay traces

`RelayTracing.allowedFor` is true when the managed policy's `limits.telemetry` is not false and `isRelayTracingEnabled(env)` is true. The websocket snapshot copies that boolean to `observability.relayTracingAllowed`.

`isRelayTracingEnabled` is false when `T3CODE_TELEMETRY_ENABLED` parses as false, or when `T3CODE_OTEL_SDK_DISABLED` or `OTEL_SDK_DISABLED` parses as true. An unset telemetry flag leaves `telemetry.value` undefined, and `undefined !== false`, so the function defaults to on. The unit test asserts `isRelayTracingEnabled({})` is true, and asserts that `T3CODE_TELEMETRY_ENABLED=false` makes relay tracing false while `otel.disabled` stays false. The product opt-out stops relay tracing and leaves the operator's own OpenTelemetry loader enabled.

Source: [otelEnvironment.ts lines 55-77 and 321-332](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/otelEnvironment.ts#L321-L332), [otelEnvironment.test.ts lines 389-418](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/otelEnvironment.test.ts#L389-L418), [ws.ts lines 1588-1591](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/ws.ts#L1588-L1591).

The web runtime builds the relay layer at module init with `isEnabled: () => relayTelemetryEnabled() === true`.

`relayTelemetryEnabled` returns true during SSR (`window` undefined). In a desktop window it reads `desktopBridge.getRelayTelemetryEnabled()` once and caches it. In a browser it returns `serverRelayTelemetry` if that has been set, otherwise true when `isHostedStaticApp()` is true, otherwise null. Null does not export, because the callback requires `=== true`.

`isHostedStaticApp` is true when no backend URL is configured and either a hosted channel is set or the page origin equals the configured hosted app URL.

`primaryRelayTracingAllowedAtom` reads the connected server's `observability.relayTracingAllowed`. Its comment says the config cache can outlive the session and predate an opt-out. `setServerRelayTelemetry` updates the browser flag after that atom changes. The desktop cache does not. A desktop window that read the bridge before an opt-out keeps the first value until the module is evaluated again.

`runtime.test.ts` stubs `T3CODE_TELEMETRY_ENABLED` to `false` and `T3CODE_OTEL_SDK_DISABLED` and `OTEL_SDK_DISABLED` to `true`, and still expects the hosted app to export `relay.first-operation`. The same test expects a browser whose server flag is false not to export, and a browser whose server flag is true to export. The test comment says the hosted app is served by no T3 server, so nothing can answer for it.

Hosted web relay traces default on. The runtime test shows they export while `T3CODE_TELEMETRY_ENABLED` is stubbed `false` and `T3CODE_OTEL_SDK_DISABLED` and `OTEL_SDK_DISABLED` are stubbed `true`. A browser connected to a T3 server follows `relayTracingAllowed` once `setServerRelayTelemetry` has run. The server sets that flag from `allowedFor`.

Source: [publicConfig.ts lines 66-95](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/cloud/publicConfig.ts#L66-L95), [runtime.ts lines 25-35](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/lib/runtime.ts#L25-L35), [hostedPairing.ts lines 34-48](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/hostedPairing.ts#L34-L48), [server.ts lines 87-92](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/state/server.ts#L87-L92), [runtime.test.ts lines 50-123](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/web/src/lib/runtime.test.ts#L50-L123).

The current user doc says the hosted web app has no tracing toggle and that managed policy does not control hosted web or mobile clients. The hosted-web half of that claim matches the code above. The mobile relay-trace gate was not fully traced in this pass.

Token and dataset values in source are configuration. This pass did not observe a production Axiom request.

## Mobile crash reports

Importing `expo-observe` installs its global JS error handler. The file's comment says reports leave only through the relay. If the relay URL is missing, `setCrashReportsEnabled(false)` runs. Otherwise, once preferences load, the app calls `setCrashReportsEnabled(preferences.crashReportsEnabled !== false)` unless a newer configuration already won. A missing preference therefore turns reporting on. The settings screen uses the same `!== false` test for the displayed switch.

Source: [observe.ts lines 1-66](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/mobile/src/features/observability/observe.ts#L1-L66).

The relay handler `relay.mobile_telemetry.ingest` reads `cf-connecting-ip`, or `"unknown"` when the header is absent, and passes that string only to `rateLimiter.allow`. On denial it returns 429. Span annotations in this function are project id, signal, byte length, outcome, and upstream status. The forwarded body is the original payload. For logs, symbolication may replace the body. On any symbolication failure the raw body is forwarded. The comment says forwarding matters more than symbolication.

This handler uses the connecting IP as a rate-limit key. The function does not write that IP into the Axiom body or into the span attributes listed above. Whether Cloudflare retains the rate-limit key or the connecting IP elsewhere is unknown hosted behavior. Exception messages and stacks are inside the Observe payload the handler forwards. The user doc says a crash report includes the error message, the stack, the app version, and the device model and OS version. That is a documentation claim consistent with forwarding the Observe body. The exact Observe schema was not re-read.

Source: [MobileTelemetry.ts lines 252-324](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/mobileTelemetry/MobileTelemetry.ts#L252-L324).

## Agent feedback

`deliver` records `agent.feedback` with `{ anonymous: true }`. The event therefore uses its own uuid as `distinct_id` and omits `installId`. Properties are `kind`, `subject`, `trace`, `userRequested`, `source`, and provider dimensions. `expected`, `actual`, and `workaround` are included only when `userRequested` is true.

Unprompted reports store `trace: null` and `userRequested: false`. They still send kind, subject, source, and provider dimensions. The written narrative is scrubbed into the local row and is not copied into the unprompted event, because those three text fields are gated on `userRequested`.

A requested report is stored only after the user answers the card. Decline settles the card and does not insert a report. `includeConversation === true` selects `conversationTrace` when present. Otherwise the outline trace is stored. `796103f4b792847561c65c921e82375a29d016c9` (2026-11-24 12:52:12 -0800, "agent feedback no longer links to the install") is an ancestor of HEAD. The current anonymous flag is proven. The full pre-change diff was not re-read. Before the flag existed, `sendBatch` attached `installId` to events that were not marked anonymous.

If telemetry refuses the event, `deliver` sets `sent` back to 0. The local row remains. The insert comment says an uncertain read is treated as sent.

Source: [FeedbackStore.ts lines 200-248 and 300-348](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackStore.ts#L200-L348).

`resolveFeedbackSubject` accepts `general`, a known `t3` CLI command, or a registered T3 tool name with provider prefixes stripped. Anything else is not a stored subject. The subject on the wire is that constrained name. It is not scrubbed, because the resolver rejects free text before storage.

Source: [FeedbackReport.ts lines 212-235](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackReport.ts#L212-L235).

`buildFeedbackTrace` without text records who spoke and which tools ran, with message length, tool outcome, and duration. It does not copy message text, tool input, or command output. With text, it adds scrubbed message text for the last turns. Caps are 80 entries, 1,000 characters per message, and 16,000 bytes for the trace. Tool names that resolve as T3 tools stay. `command_execution` becomes `shell`. For Claude and Codex, a built-in-shaped name that is not an integration and does not start with `mcp` is kept. Every other dynamic tool becomes the constant `mcp`.

Source: [FeedbackTrace.ts lines 7-48 and 65-157](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackTrace.ts#L7-L157).

`scrubFeedbackText` redacts credential URLs (`scheme://user@`), a list of token prefixes, JWTs, emails, quoted and unquoted paths through the rest of the line, long high-entropy runs of at least 32 characters, and caller-supplied sensitive strings of at least 3 characters, matched with word boundaries. A known value that contains newlines is matched line by line. Plain `https://` URLs without userinfo are not in the credential pattern and are not in the path pattern. They survive unless they happen to match another rule. The scrubber does not know source code or names written in a sentence.

The sensitive list passed at submit time is thread id, project id, home directory, username, hostname, worktree path, branch, workspace root, project title, repository remote and web URLs, canonical key, and `owner/name`.

Source: [scrubFeedback.ts lines 7-123](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/scrubFeedback.ts#L7-L123) and [FeedbackService.ts lines 120-160](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/feedback/FeedbackService.ts#L120-L160).

The local table is `agent_feedback`, including thread id, and the trace JSON. That row is on disk even when the analytics send is anonymous.

## Agent activity publishing

Publishing runs only when the secret `cloud-publish-agent-activity` is exactly the string `true`, and the relay URL and environment credential are non-empty. Any other secret value, including empty, is off. `T3CODE_TELEMETRY_ENABLED` is not an input to `isAgentActivityPublishingEnabledValue`.

Source: [config.ts lines 18 and 43-75](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/cloud/config.ts#L43-L75).

`projectThreadAwarenessV2` builds `environmentId`, `threadId`, `project.title`, `thread.title`, a phase, a fixed headline, an optional detail, `thread.modelSelection.model` unchanged, `updatedAt`, and a deep link. The deep link is `/threads/<environmentId>/<threadId>` only. It does not contain a hostname. `modelTitle` is the raw model id, not `modelLabel`. A local model path that product analytics would reduce to a basename is published in full when this channel is on.

`sanitizeRelayAgentActivityState` replaces a failed detail with "The agent run failed." and truncates detail to 160 characters. It does not scrub titles or `modelTitle`.

The relay schema stores that state in Postgres `state_json`.

Source: [agentAwareness.ts lines 77-151](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/shared/src/agentAwareness.ts#L77-L151), [relay.ts lines 119-130](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/packages/contracts/src/relay.ts#L119-L130), [AgentAwarenessRelay.ts lines 206-224](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/relay/AgentAwarenessRelay.ts#L206-L224), [schema.ts line 157](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/infra/relay/src/persistence/schema.ts#L157).

Whether a given install has the secret set is unknown. Hosted retention of `state_json` is unknown. The code path is proven. A default install does not publish, because the gate requires the string `true`.

## Local storage and the configured provider

Under the state directory, `deriveServerPaths` creates `statev2.sqlite`, `attachments/`, `logs/server.trace.ndjson`, `logs/provider/events.log`, `logs/terminals/`, `anonymous-id`, `environment-id`, `settings.json`, and `secrets/`. Conversation text and projections live in that SQLite database. This layout is local. The product sender cited above does not read those files into the POST body.

`EventNdjsonLogger` writes rotating local provider logs. Defaults in the module header are 10 MiB files, 10 files, 512 MiB total, 14 days, and records capped at 64 KiB, 1,024 fields, and depth 16. The header does not describe an upload. This pass did not find a sender inside that module. A repo-wide claim that no diagnostic bundle exists was not re-established.

`otlpResource` is the operator's own collector resource. It sets `host.name` from `OTEL_RESOURCE_ATTRIBUTES` or the machine hostname, and it keeps the operator's `service.instance.id` when one is set. That resource is not the relay exporter. A user who configures `OTEL_EXPORTER_OTLP_*` is sending that resource to their own endpoint. Product telemetry opt-out does not disable that loader, as the relay-tracing test above shows by leaving `otel.disabled` false.

Source: [config.ts lines 125-180](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/config.ts#L125-L180) and [EventNdjsonLogger.ts lines 28-40](https://github.com/pingdotgg/t3code/blob/55085df2a6c384f34b37901d5dcbc5925ada1600/apps/server/src/provider/EventNdjsonLogger.ts#L28-L40).

Prompts and files the user sends to a model go to the provider that user configured. This pass did not read a driver function that builds that HTTP body, so the exact bytes are not cited. Product events cited above do not include message text. Feedback text leaves only through the anonymous feedback path, and only after the gates in that section.

Auth sessions store a client label, OS, and device type in local SQLite. That column was seen in `AuthSessions.ts` and is not copied by `readClientAnalyticsProps`. ChatGPT emails remain in the local credential registration. The analytics event stores counts.

## Findings

Proven at HEAD:

1. Product events default on and POST to `https://ingest.t3.codes/batch/` with a compiled-in `phc_` key. Person profiles are disabled in the client JSON.
2. `distinct_id` and `installId` are the same unsalted SHA-256 of a random file. Connect and device owners are unsalted hashes. Raw provider account files are not read.
3. Every product event can include the raw `WSL_DISTRO_NAME`. Mobile events can include `Device.modelName` up to 80 characters. Web events can include a browser string up to 64 characters.
4. `modelLabel` sends a non-path custom model id unchanged, including a URL. A path model id is reduced to its basename on the product path only.
5. `t3_thread_send` handoff analytics copies `delivery` with no allow-list.
6. Hosted web relay traces default on and ignore `T3CODE_TELEMETRY_ENABLED` and both OTEL disable flags. Connected browsers follow the server flag after it is delivered. Desktop caches the bridge flag once.
7. Relay exports keep `url.path` and `environment.id` on connection attempts. The unit test shows address, query, host resource name, log text, and error message and stack absent from the sample payload.
8. Mobile crash reporting defaults on when the preference is omitted and a relay URL exists. The relay forwards the Observe body. The connecting IP is a rate-limit key in that handler.
9. Agent feedback on the wire is anonymous. Unprompted events omit the narrative. Requested conversation text requires an approval and `includeConversation`. The scrubber keeps bare `https://` URLs. The local row keeps the thread id.
10. Activity publishing is default off, is not tied to the telemetry opt-out, and when enabled sends titles and the raw model id to relay Postgres.

Proven historical, removed in HEAD, still true of older builds and of events already stored:

1. Before `84e4264`, unsalted hashes of Codex `account_id` (legacy `distinct_id`), OpenAI `user_id` (owner), Claude `userID` (legacy `distinct_id` fallback), and Claude `accountUuid` (owner), read from local auth files. Team-shared `account_id` is stated in the parent comment.
2. Before `482e197`, the mobile analytics device hash was the relay device id.
3. Before `3ba003be`, Windows desktop did not copy or read a User or Machine `T3CODE_TELEMETRY_ENABLED`.
4. Before `796103f`, feedback was not marked anonymous, so `sendBatch` attached `installId`.
5. Before `dc7b880`, the relay exporter and the user doc still described machine details that HEAD strips. The full parent exporter was not re-diffed line by line in this pass. The current test and the current doc are the HEAD evidence.

Hypothesis or unknown:

1. Ingest or the HTTP stack records client IP and User-Agent. The client JSON does not contain them. Ingest code is absent.
2. PostHog honors `$process_person_profile: false`. The client sets the field.
3. Cloudflare retains `cf-connecting-ip` beyond the rate-limit decision this handler makes.
4. `EnvironmentSupervisor.make` can put `environment.label` on some exported span other than `relay.connection.attempt`.
5. `t3_thread_send`'s `delivery` string is constrained by a tool result schema this pass did not read.
6. The emitter of dump event `client.connected`. It is absent from this tree.
7. Retention, deletion of old account hashes, and the deployed worker version.

## Corrections to ANALYSIS.md

`ANALYSIS.md` at report-repo SHA `b68d587` is a dump analysis plus a short code note. Its event counts, token totals, and identifier counts were not recomputed here. Treat them as that document's results. The gzip hash of the dump file matches the hash recorded for this assessment.

Corrections that the code supports:

- The owner-hash sentence merges inputs. OpenAI owner events used `user_id` from the unverified id token. The legacy `distinct_id` used Codex `account_id`, which the parent says a Team shares. Claude owner events used `accountUuid`. Claude `userID` was the `distinct_id` fallback and is described as random per machine.
- The machine-name sentence quotes documentation from commit `11edf884`. At `55085df`, `docs/user/telemetry.md` lines 68-71 say traces omit machine addresses, query strings, log lines, error messages, and stack frames. The exporter test supports that for the keys and the error text it asserts, and it also shows that `url.path` is kept. Builds from before `dc7b880` are a different program.
- `scripts/analyse.py` lines 65-73 walk top-level `properties` values and `user_agent`. A nested object is skipped because the scan requires `typeof` string. The script comment says "every string value". The loop does not descend. `ANALYSIS.md` now calls this a limited pattern scan. That limitation is the loop, not only the regex list.
- Current code sends `WSL_DISTRO_NAME` on every product event from a WSL process, and sends length-capped `clientDeviceModel` and `clientBrowser`. `ANALYSIS.md` now says custom model ids and device labels appear in the export. This assessment did not check whether the dump contains `wsl` or `serverWslDistro`.
- `client.connected` is in the dump table and is not in this source tree. Do not describe its properties from the current `readClientAnalyticsProps` as if this snapshot emitted it. The query-parameter reader is what current sockets attach to the events that still exist.

`ANALYSIS.md` is right that the dump is one user's product stream, that unsalted hashes are recomputable by someone who holds the raw id, that ingest IP logging is not visible in the export, and that the same-day commits `84e4264`, `482e197`, `3ba003be`, and `796103f` changed identity, the mobile device id, the Windows opt-out, and feedback linkage. Those commit messages match the diffs read here. The relay machine-detail removal is the additional commit `dc7b880`, which the findings section of `ANALYSIS.md` does not list.

## Limits

- Shallow clone of 100 commits. Removals whose parents are present are proven. Introductions older than the clone are not.
- No re-parse of `data/t3code-telemetry-events-jsonl-a4896cdc.gz`, and no read of `results/extras.json` in this pass.
- No live auth files, conversations, or local database.
- No capture of traffic to ingest, PostHog, Axiom, or a model provider.
- `apps/mobile/src/features/observability/tracing.ts` was not read in full, so the interaction between "Send crash reports" and mobile relay traces is not stated as proven.
- One provider driver request builder was not read, so provider request bodies are not cited.
- Desktop crash reporting was not traced. A search for Sentry, Bugsnag, and Datadog was not repeated in this pass. Do not treat that absence as a finding.
- Tests cited were read. They were not re-executed.

## Commands

```
git -C t3code-source rev-parse HEAD
git -C t3code-source rev-parse --is-shallow-repository
git -C t3code-source rev-list --count HEAD
git -C t3code-source merge-base --is-ancestor 84e4264bb347e36e97f6c3bd95d666eecfa12e07 HEAD
git -C t3code-source show 54ba2408f452705a5e43ce3dbdc878b6eeefded4:apps/server/src/telemetry/Identify.ts
git -C t3code-source grep -n client.connected -- '*.ts' '*.tsx' '*.md'
shasum -a 256 report-repo/data/t3code-telemetry-events-jsonl-a4896cdc.gz
```

The `client.connected` grep over `*.ts`, `*.tsx`, and `*.md` returned no matches. The gzip sha256 matched the hash in the table above.
