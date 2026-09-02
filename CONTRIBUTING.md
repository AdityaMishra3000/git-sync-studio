# Contributing

## The loop

```text
issue -> branch -> implement -> tests -> PR -> review -> merge
```

Nothing is pushed to `main`. Every merge is a reviewed pull request, because the
project is assessed on individual contribution and a shared branch erases it.

## Branches

One branch per issue, named after the work:

```text
feat/github-webhook-receiver
feat/pr-feature-extraction
feat/drive-resumable-upload
fix/health-probe-timeout
chore/pin-ruff-0.16
docs/adr-drive-pointer-format
```

Rebase onto `main` before asking for review. Merge conflicts are the author's to
resolve, not the reviewer's.

## Commits

Conventional commits, scoped to the module:

```text
feat(github): verify X-Hub-Signature-256 on the webhook receiver
feat(prediction): add temporal split trainer
fix(drive): resume an interrupted upload from the session URI
test(readme): cover the missing-evidence path
chore(ci): run mypy on the worker package
docs(adr): record the Drive pointer format
```

The subject says what changed, in the imperative, under ~72 characters. The body
says **why**, when why is not obvious. One logical change per commit: a commit
that renames a module _and_ adds a feature cannot be reviewed or reverted.

No `wip`, no `fix fix`, no single commit containing an entire phase.

## Pull requests

The template asks for what changed, how it was verified, and what a reviewer
should push back on. Fill in all three. "Tests pass" is not a verification note -
say what you ran and what it printed.

Before opening:

```bash
make lint typecheck test
```

Keep them reviewable. If a PR is over roughly 400 changed lines, it is usually two
PRs.

## Review

The reviewer is looking for: does it do what the issue asked, is the failure path
handled, is it tested, does it stay inside its module boundary, and does it belong
to the current phase. Work from a later phase gets split out, not merged early.

Approve or request changes - not both, and not silence. A PR waiting more than a
day is a process failure, not an author failure.

## Tests are part of the change

A pull request that adds behaviour without a test does not get merged. At minimum:
one test for the happy path and one for the failure the code is written to
survive. `make test` has to pass before review, not after.

## Definition of Done per phase

Each phase has one in [docs/roadmap.md](docs/roadmap.md), and it must be
_demonstrable_ - a command someone else can run. PHASE 0's is
`./scripts/dev/verify-phase-0.sh`. Later phases add their own script in
`scripts/dev/`.

## Secrets

Never commit `.env`, a `.pem`, an OAuth client secret, a token, or a service
account JSON. `.gitignore` blocks the obvious names and `verify-phase-0.sh`
asserts that nothing matching them is tracked, but neither is a substitute for
looking at your own diff.

If a secret is committed: rotate it first, then rewrite history. A deleted secret
is still in the reflog and still on GitHub.

Optional local guard:

```bash
pip install pre-commit && pre-commit install
```

## Repository settings (do this once, on GitHub)

Settings -> Branches -> add a rule for `main`:

- require a pull request before merging, with at least 1 approval
- require the `backend`, `frontend` and `stack` status checks to pass
- require branches to be up to date before merging
- do not allow force pushes or deletions

Without these, the workflow above is a convention people forget under deadline.
