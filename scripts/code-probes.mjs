import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { stripTypeScriptTypes } from 'node:module';
import { execFileSync } from 'node:child_process';

const sourceRoot = resolve(process.argv[2] ?? 't3code-source');
const revision = execFileSync('git', ['-C', sourceRoot, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
assert.equal(revision, '55085df2a6c384f34b37901d5dcbc5925ada1600');
const read = (name) => readFileSync(resolve(sourceRoot, name), 'utf8');
const results = { revision, method: 'Offline source-fragment execution with synthetic inputs. No network or full application runtime.' };

const { scrubFeedback } = await import(pathToFileURL(resolve(sourceRoot, 'apps/server/src/feedback/scrubFeedback.ts')).href);
results.feedback = ['email user@example.com', 'Read /Users/example/private.txt', 'Patient Alice has diabetes', 'password=hunter2'].map(input => ({ input, output: scrubFeedback(input, []) }));
assert.equal(results.feedback[0].output, 'email [redacted]');
assert.equal(results.feedback[1].output, 'Read [redacted]');
assert.equal(results.feedback[2].output, results.feedback[2].input);
assert.equal(results.feedback[3].output, results.feedback[3].input);

// Empty catalog isolates the unknown-model branch. The source functions are unchanged.
const dimensions = read('apps/server/src/telemetry/ProviderDimensions.ts').replace(/^import[\s\S]*?;\n/gm, '');
const modelModule = stripTypeScriptTypes('const BUNDLED_MODEL_MANIFEST={providers:{}};\n' + dimensions);
const { modelLabel } = await import('data:text/javascript;base64,' + Buffer.from(modelModule).toString('base64'));
results.models = ['/Users/example/customer-acme.gguf', 'models/customer-acme.gguf', 'acme-private-model'].map(input => ({ input, output: modelLabel([], input) }));
assert.equal(results.models[0].output, 'customer-acme.gguf');
assert.equal(results.models[1].output, results.models[1].input);
assert.equal(results.models[2].output, results.models[2].input);

// Execute the actual payload expression, with dependencies supplied as synthetic values.
// This proves serialization and shared-envelope linkability, not network delivery or retention.
const analytics = read('apps/server/src/telemetry/AnalyticsService.ts');
const start = analytics.indexOf('    const payload = {');
const end = analytics.indexOf('\n    yield* HttpClientRequest.post', start);
assert(start >= 0 && end > start);
const serialize = new Function('events', 'distinctId', 'installId', 'telemetryConfig', 'Option', 'hostPlatform', 'hostArchitecture', 'packageJson', 'ServerConfig', 'clientType', 'serverOsFromNodePlatform', 'serverConfig', analytics.slice(start, end) + '\nreturn payload;');
const events = [
  { uuid: 'identified-event', event: 'provider.turn.completed', properties: {}, capturedAt: 'synthetic-time' },
  { uuid: 'feedback-event', event: 'agent.feedback', properties: { kind: 'bug' }, capturedAt: 'synthetic-time', anonymous: true },
];
const payload = serialize(events, 'synthetic-install', 'synthetic-install', { posthogKey: 'synthetic-public-key', wslDistroName: 'customer-acme-work' }, { getOrUndefined: value => value }, 'linux', 'x64', { version: 'test' }, { telemetryChannel: 'test' }, 'desktop-app', () => 'Linux', { mode: 'desktop' });
assert.equal(payload.batch.length, 2);
assert.equal(payload.batch[0].properties.installId, 'synthetic-install');
assert.equal(payload.batch[1].distinct_id, 'feedback-event');
assert.equal(payload.batch[1].properties.installId, undefined);
assert.equal(payload.batch[1].properties.serverWslDistro, 'customer-acme-work');
results.batch = payload.batch;
console.log(JSON.stringify(results, null, 2));
