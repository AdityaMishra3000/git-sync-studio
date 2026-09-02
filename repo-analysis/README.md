# repo-analysis/

Deterministic repository analysis that feeds the README generator. **PHASE 5.**

Planned layout:

```text
extractors/   GitHub metadata, file tree, git history, contributors
parsers/      package.json, pyproject.toml, requirements.txt, Dockerfile,
              compose.yaml, GitHub workflow files
heuristics/   entry points, test framework, package manager, exposed ports
readme/       evidence package assembly and section templates
```

The output is an **evidence package**: a structured record of what was actually
found, each item carrying the file and line it came from. The generator may only
state what the evidence supports; anything unsupported is rendered as
"Not identified from repository evidence" rather than guessed.

That constraint is what separates this from asking a model to write a README. A
generated install command that does not work is worse than no install command,
because a reader will run it.

Tree-sitter is used only where a real parse beats a regex (entry points, exported
symbols). Configuration files are parsed with their own format's parser, not
pattern-matched.
