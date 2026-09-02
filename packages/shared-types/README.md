# @gitsync/shared-types

The TypeScript view of the API contract. Consumed by `apps/web` through the npm
workspace and transpiled by Next.js (`transpilePackages`), so the package ships
raw `.ts` - there is no build step.

```ts
import type { HealthResponse } from "@gitsync/shared-types";
```

## Source of truth

`apps/api` is the source of truth. These types are a hand-written mirror of the
Pydantic schemas, which means they **can** drift.

From PHASE 1, when the API starts returning domain entities, generate them from
the live OpenAPI document instead:

```bash
npx openapi-typescript http://localhost:8000/api/v1/openapi.json -o packages/shared-types/src/generated/api.ts
```

Then keep `src/health.ts`-style files only for things the schema cannot express.
Hand-mirroring two or three response shapes in PHASE 0 is cheaper than wiring a
codegen step before there is anything to generate.

## Conventions

- Field names stay `snake_case`: they are exactly what the API sends.
- `type`/`interface` only, no runtime code. Anything executable belongs in the
  app that needs it.
- One file per API module (`health.ts`, later `repository.ts`, `pull-request.ts`,
  `prediction.ts`, `large-object.ts`, `readme.ts`), re-exported from `index.ts`.
