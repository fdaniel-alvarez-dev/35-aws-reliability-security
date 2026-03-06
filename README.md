# 35-aws-reliability-security-mysql

A portfolio-grade, runnable reliability + security toolkit for **MySQL operations**:
replication health checks, safe backup/restore drills, and deterministic validation.

This repository is intentionally generic (no employer branding). It focuses on working automation, not claims.

## The 3 core problems this repo solves
1) **Recovery you can trust:** backup + restore drills that are verifiable and safe to rerun.
2) **Replication confidence:** repeatable checks for replica health and “is it actually syncing?”.
3) **Production-safe validation:** explicit test modes that separate offline checks from integration tests.

## Quickstart (local lab)
Prereqs: Docker + Docker Compose.

```bash
make demo
```

You get:
- MySQL primary + replica (replication configured)
- scripts to seed data, verify replication, and run backup/restore drills

## Tests (two explicit modes)

This repo supports exactly two test modes via `TEST_MODE`:

- `TEST_MODE=demo` (default): offline-only, deterministic guardrails (no Docker required)
- `TEST_MODE=production`: real Docker integrations (guarded by explicit opt-in)

Run demo mode:

```bash
make test-demo
```

Run production mode:

```bash
make test-production
```

## Guardrails

The file `tools/mysql_guardrails.py` performs offline checks to ensure the repo stays honest:
- docker-compose defines MySQL services and avoids floating image tags
- restore drills are isolated (verification DB)
- README documents `TEST_MODE`

Generate a JSON report:

```bash
python3 tools/mysql_guardrails.py --format json --out artifacts/mysql_guardrails.json
```

## Sponsorship and contact

Sponsored by:
CloudForgeLabs  
https://cloudforgelabs.ainextstudios.com/  
support@ainextstudios.com

Built by:
Freddy D. Alvarez  
https://www.linkedin.com/in/freddy-daniel-alvarez/

For job opportunities, contact:
it.freddy.alvarez@gmail.com

## License

Personal, educational, and non-commercial use is free. Commercial use requires paid permission.
See `LICENSE` and `COMMERCIAL_LICENSE.md`.
