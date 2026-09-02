# cli/

The `gitsync` command-line client (Python + Typer). **PHASE 4.**

Planned layout:

```text
gitsync/commands/   init, login, add, pull, status, fetch
gitsync/filters/    git clean/smudge filter implementation
gitsync/cache/      ~/.gitsync/cache/<oid>, verified by SHA-256
```

Planned surface:

```bash
gitsync init          # register the filter and .gitattributes patterns
gitsync login         # obtain an API session
gitsync add <file>    # hash, dedupe, upload to Drive, write a pointer
gitsync pull          # resolve pointers in the working tree to real bytes
gitsync status        # what is a pointer, what is materialised
gitsync fetch <oid>   # fetch one object by content hash
```

The CLI talks to the **API**, never to Google Drive directly. That keeps the
Drive refresh token on the server, keeps PostgreSQL authoritative for the
object-to-file mapping, and means a revoked account revokes every client at once.

This is a Git-LFS-_inspired_ pointer system, not an implementation of the Git LFS
transfer protocol. A custom transfer adapter is a stretch goal, explicitly out of
the MVP.
