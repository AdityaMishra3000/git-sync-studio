# Roadmap

Phases land in order. A phase is finished when its Definition of Done is
demonstrable, not when the code exists. Nothing from a later phase gets built
early - that is what keeps the project deliverable.

| Phase  | Delivers                                                      | Definition of Done                                                                        | Status                    |
| ------ | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------- |
| **0**  | Monorepo, Docker Compose, health endpoints, lint/type/test    | `docker compose up` brings up five healthy services; the API reports on all three deps    | **Done**                  |
| **1**  | `users` + `repositories`, `GET/POST /api/v1/repos`, dashboard | Browser to Next.js to FastAPI to PostgreSQL and back; records survive a restart           | Next                      |
| **2**  | GitHub App, installation auth, repo sync, webhooks            | Open a PR on GitHub; it appears in the dashboard within seconds via a verified webhook    | Not started               |
| **3**  | PR feature extraction, temporal-split training, predictions   | A model artefact is versioned; a PR gets a probability, a time bucket and reasons         | Not started               |
| **4**  | Google OAuth, Drive uploads, pointers, `gitsync` CLI          | A >100 MiB file lives in Drive, Git holds only the pointer, another checkout resolves it  | Not started               |
| **5**  | Repository evidence extraction, README generation             | A deterministic README draft with warnings, reviewed and approved by a human              | Not started               |
| **6**  | Real background jobs, retries, job tracking, reconciliation   | Long operations never block HTTP; jobs are inspectable and retryable; duplicates are safe | Not started               |
| **7**  | Auth, RBAC, encrypted tokens, rate limits, audit logs         | No secret in git, no unsigned webhook trusted, no refresh token in a browser              | Not started               |
| **8**  | Unit, integration, contract, E2E, ML and failure-path tests   | Every layer covered, including interrupted uploads and replayed webhooks                  | Continuous                |
| **9**  | Full CI/CD: security scans, GHCR images, migrations, deploy   | Green pipeline on every PR; protected `main`; deployed image passes a smoke test          | Partial (lint/test/stack) |
| **10** | One repository flowing through the whole system               | The demo script runs end to end without a detour                                          | Not started               |

## Scope decisions that are already made

These are settled. Reopening them costs weeks the project does not have.

- **Modular monolith**, not microservices. One FastAPI application, one worker.
- **Git-LFS-inspired**, not a Git LFS server. No custom transfer adapter in the MVP.
- **Tabular models** for prediction (logistic regression baseline, then random
  forest / gradient boosting). No transformers, no PyTorch.
- **Temporal splits only.** A random train/test split leaks future repository
  behaviour into training and inflates every metric.
- **Predictions are advisory.** Never an automatic accept, reject, or ranking of
  contributors.
- **The README generator never invents facts.** No evidence means the draft says
  so explicitly, and a human approves before anything is written.
- **PostgreSQL and FastAPI are fixed.** So are Next.js, Redis and Celery.

## Stretch goals - only after PHASE 10

Custom Git LFS transfer adapter, LightGBM/XGBoost, semantic PR embeddings, Drive
`changes.watch` push notifications, deeper static analysis, Kubernetes.
