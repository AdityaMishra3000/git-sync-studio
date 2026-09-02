## What and why

<!-- One paragraph: what this changes and why it is needed. Link the issue. -->

Closes #

## Phase

<!-- Which phase does this belong to? Work that belongs to a later phase does
     not get merged early - split it out. -->

- [ ] PHASE 0 foundation
- [ ] PHASE 1 application skeleton
- [ ] PHASE 2 GitHub
- [ ] PHASE 3 PR predictor
- [ ] PHASE 4 Drive large files
- [ ] PHASE 5 README generator
- [ ] PHASE 6 workers and integration
- [ ] PHASE 7 security
- [ ] PHASE 8 testing
- [ ] PHASE 9 CI/CD
- [ ] Fix / chore / docs

## How it was verified

<!-- Commands you actually ran and what they printed. "Tests pass" is not a
     verification note. -->

```

```

## Checklist

- [ ] `make lint`, `make typecheck` and `make test` pass locally
- [ ] Tests cover the new behaviour, including at least one failure path
- [ ] No secrets, tokens, keys or `.env` files in the diff
- [ ] Public behaviour changes are documented (`docs/`, README, or docstrings)
- [ ] Migrations are reversible and were tested with `alembic downgrade`
- [ ] The commit history is readable: conventional commits, no "fix fix wip"

## Anything a reviewer should push back on

<!-- Shortcuts taken, technical debt added, decisions you are unsure about.
     Saying "none" here is usually wrong. -->
