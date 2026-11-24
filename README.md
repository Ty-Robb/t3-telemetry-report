# Theo's T3 Code telemetry dump: analysis

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
