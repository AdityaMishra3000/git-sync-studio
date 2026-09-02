# scripts/

```text
dev/bootstrap.sh         one-time setup for a fresh clone
dev/verify-phase-0.sh    the PHASE 0 Definition of Done, executable
seed/                    demo and fixture data (PHASE 1+)
```

Two rules: every script is safe to run twice, and every script says what it is
doing. A script that silently mutates a database is a script nobody will run.

## seed/

Empty until PHASE 1 creates something to seed. It will hold the demo repository
fixtures used by `docs/roadmap.md`'s PHASE 10 walkthrough - deterministic data,
so a demo does not depend on GitHub being reachable at the wrong moment.
