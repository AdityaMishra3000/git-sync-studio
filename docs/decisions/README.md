# Architecture decision records

One file per decision that would otherwise be re-argued every few weeks. Format:
context, decision, consequences. Numbered, immutable once merged - a decision
that turns out wrong gets a new record that supersedes it, not an edit.

Write one when a choice is **expensive to reverse** (a datastore, a boundary, a
protocol) or when the obvious-looking alternative was rejected for a reason that
is not visible in the code. Do not write one for a library pick that a `git
revert` undoes.

| ADR                                            | Decision                                                               |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| [0001](0001-modular-monolith-in-a-monorepo.md) | Modular monolith in a monorepo, one Python codebase for API and worker |
