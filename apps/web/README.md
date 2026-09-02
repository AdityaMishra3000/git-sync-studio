# apps/web

Next.js (App Router) frontend, TypeScript, Tailwind v4, shadcn/ui.

```bash
docker compose up web         # http://localhost:3100
npm run dev --workspace=web   # or run it directly, on :3000
```

## Layout

```text
app/                  routes. `/` and `/dashboard` exist today.
components/           application components
components/ui/        shadcn/ui primitives - regenerate, do not hand-edit
lib/api.ts            typed access to the FastAPI backend
lib/health.ts         pure presentation helpers (unit tested)
types/index.ts        the app's type surface; re-exports the shared contract
hooks/                client hooks (empty until there is client state)
tests/unit/           vitest + Testing Library
tests/e2e/            Playwright, against a running stack
```

Routes for repositories, pull requests, files, README and settings arrive with
their phases. Navigation deliberately lists only routes that exist.

## Conventions

- **Server components fetch.** Pages read from the API on the server using
  `API_INTERNAL_BASE_URL` (`http://api:8000` under Compose). A client component
  is justified by interaction, not by data loading.
- **`lib/api.ts` never throws.** Failures come back as data
  (`{ reachable: false, error }`) so a page renders a useful message instead of an
  error boundary. An HTTP 503 from `/health` is a _valid report_, not a failure.
- **Only `NEXT_PUBLIC_*` reaches the browser.** Anything secret stays in a server
  component or a route handler.
- **Types come from `@/types`**, which re-exports `@gitsync/shared-types`. Field
  names stay `snake_case` because that is what the API sends.
- **Colour is never the only signal.** Status uses a reserved four-step palette on
  an icon, with the state also written out in text, and the text keeps its own
  colour token so contrast does not depend on the status hue.

## Checks

```bash
npm run lint --workspace=web
npm run typecheck --workspace=web       # next typegen && tsc --noEmit
npm test --workspace=web                # vitest
npm run test:e2e:install --workspace=web  # once
E2E_BASE_URL=http://localhost:3100 npm run test:e2e --workspace=web
```

## Adding a shadcn/ui component

```bash
npx shadcn@latest add <component>
```

It writes into `components/ui/`. Those files are ours to keep but not to edit by
hand - customise through `className`, or wrap the primitive in `components/`.
