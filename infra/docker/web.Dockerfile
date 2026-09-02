# syntax=docker/dockerfile:1
#
# Next.js web image.
#
# Build context is the repository ROOT because this is an npm workspace: the app
# needs the root lockfile and the `packages/shared-types` workspace package.
#   docker build -f infra/docker/web.Dockerfile --target dev .

FROM node:24-alpine AS base

ENV NEXT_TELEMETRY_DISABLED=1
# Next.js prebuilt binaries expect glibc symbols.
RUN apk add --no-cache libc6-compat
WORKDIR /app
# Own the tree as `node` (uid 1000) from the start: installing as root and
# chown-ing 800+ packages afterwards costs a minute and a half per build.
RUN chown node:node /app

# --------------------------------------------------------------------------
# Dependencies. Only the manifests are copied so this layer survives source
# edits; `npm ci` installs the whole workspace from the committed lockfile.
# --------------------------------------------------------------------------
FROM base AS deps

USER node
COPY --chown=node:node package.json package-lock.json ./
COPY --chown=node:node apps/web/package.json apps/web/package.json
COPY --chown=node:node packages/shared-types/package.json packages/shared-types/package.json
RUN npm ci

# --------------------------------------------------------------------------
# Development target: `next dev`, source bind-mounted by compose.
# --------------------------------------------------------------------------
FROM deps AS dev

COPY --chown=node:node . .
# compose mounts anonymous volumes over these two paths, and a volume inherits
# the ownership of the image directory underneath it. Both are .dockerignore'd,
# so create them here as `node` or the dev server cannot write its build cache.
RUN mkdir -p /app/apps/web/.next /app/apps/web/node_modules
WORKDIR /app/apps/web
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

# --------------------------------------------------------------------------
# Production build. `output: "standalone"` (next.config.ts) emits a self
# contained server plus only the node_modules it actually traced.
# --------------------------------------------------------------------------
FROM deps AS builder

COPY --chown=node:node . .
RUN npm run build --workspace=web

FROM base AS runtime

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# `node` (uid 1000) already exists in the base image; reuse it instead of
# inventing another unprivileged user.
COPY --from=builder --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=builder --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=node:node /app/apps/web/public ./apps/web/public

USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
