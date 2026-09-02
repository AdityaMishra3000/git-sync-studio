# Documentation

| Document                                             | What it covers                                               |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| [development.md](development.md)                     | Running the stack, ports, everyday commands, troubleshooting |
| [roadmap.md](roadmap.md)                             | The phases, what each delivers, and its Definition of Done   |
| [architecture/overview.md](architecture/overview.md) | Runtime topology, module boundaries, target tree             |
| [api/README.md](api/README.md)                       | Endpoint inventory and where the OpenAPI document lives      |
| [decisions/](decisions/)                             | Architecture decision records                                |

Two rules for this directory:

1. **Documentation follows working code.** A document describing something that
   does not run yet belongs in `roadmap.md` as a plan, not here as a description.
2. **Say why, not what.** The code already says what it does. Docs exist for the
   reasoning that the code cannot carry.
