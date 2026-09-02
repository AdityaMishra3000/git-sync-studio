# hooks/

Client-side React hooks. Empty in PHASE 0 by design: every page so far is a
server component that fetches on the server, so there is no client state to
share yet.

Expected residents:

- `use-repositories.ts` - repository list / mutations (PHASE 1)
- `use-pull-requests.ts` - PR list with polling for webhook-driven updates (PHASE 2)
- `use-upload.ts` - large-file upload progress (PHASE 4)

Keep data fetching in server components unless the UI genuinely needs client
state; a hook that only wraps `fetch` on mount is a step backwards from a server
component.
