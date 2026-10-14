from __future__ import annotations

from app.readme.models import ReadmeDetailLevel, RepositoryEvidence


def generate_mermaid_diagram(evidence: RepositoryEvidence) -> str:
    """Generate a Mermaid architecture diagram representing verified component interactions."""
    if not evidence.architecture_components:
        return ""

    lines = ["```mermaid", "flowchart TD"]

    # Component nodes
    node_ids: dict[str, str] = {}
    for i, comp in enumerate(evidence.architecture_components):
        nid = f"comp_{i}"
        node_ids[comp.name] = nid
        tech_sub = f"<br/><i>({', '.join(comp.technologies[:2])})</i>" if comp.technologies else ""
        lines.append(f'    {nid}["{comp.name}{tech_sub}"]')

    # External/Infra nodes if services exist
    infra_names = {"postgres", "redis", "postgres-db", "redis-broker"}
    for i, svc in enumerate(evidence.services):
        if svc.name not in node_ids and svc.name in infra_names:
            nid = f"infra_{i}"
            node_ids[svc.name] = nid
            lines.append(f'    {nid}[("{svc.name.upper()}<br/><i>Service</i>")]')

    # Relationships
    for rel in evidence.relationships:
        s_id = node_ids.get(rel.source)
        t_id = node_ids.get(rel.target)
        if s_id and t_id:
            lbl = rel.relationship_type.replace('"', "")
            lines.append(f'    {s_id} -->|"{lbl}"| {t_id}')

    lines.append("```")
    return "\n".join(lines)


def build_sections(
    evidence: RepositoryEvidence, detail_level: ReadmeDetailLevel = "detailed"
) -> dict[str, str]:
    """Generate discrete, independent Markdown sections grounded in repository evidence."""
    sections: dict[str, str] = {}
    name = evidence.name
    desc = evidence.description or f"Workspace intelligence platform for {name}."

    # 1. Identity & Overview
    overview_lines = [
        f"# {name}",
        "",
        desc,
        "",
    ]
    if evidence.primary_language:
        top_langs = [f"{k} ({v}%)" for k, v in list(evidence.languages.items())[:3]]
        overview_lines.append(
            f"**Primary:** {evidence.primary_language} · **Languages:** {', '.join(top_langs)}"
        )
        overview_lines.append("")
    if evidence.frameworks:
        badges = " ".join([f"`{f}`" for f in evidence.frameworks])
        overview_lines.append(f"**Frameworks & Libraries:** {badges}")
        overview_lines.append("")

    sections["overview"] = "\n".join(overview_lines).strip()

    # 2. Features
    feature_lines = ["## Features", ""]
    if evidence.is_monorepo:
        count = len(evidence.monorepo_workspaces)
        feature_lines.append(
            f"- **Monorepo Architecture:** Organized across {count} workspace packages."
        )
    if any("FastAPI" in f for f in evidence.frameworks):
        feature_lines.append(
            "- **High-Performance REST API:** Built with FastAPI, utilizing asynchronous handlers."
        )
    if any("Next.js" in f or "React" in f for f in evidence.frameworks):
        feature_lines.append(
            "- **Modern Web Interface:** Interactive dashboards with Next.js and Tailwind CSS."
        )
    if evidence.background_workers:
        workers_str = ", ".join(evidence.background_workers)
        feature_lines.append(
            f"- **Async Task Queue:** Distributed job processing via {workers_str}."
        )
    if evidence.database_technologies:
        db_str = ", ".join(evidence.database_technologies)
        feature_lines.append(f"- **Persistence:** Enterprise data storage via {db_str}.")
    if evidence.services:
        svc_count = len(evidence.services)
        feature_lines.append(
            f"- **Containerized Stack:** Orchestrated via Docker Compose ({svc_count} services)."
        )
    if len(feature_lines) == 2:
        feature_lines.append(
            "- **Application Engine:** Modular architecture structured for maintainability."
        )

    sections["features"] = "\n".join(feature_lines).strip()

    # 3. Architecture & Data Flow
    arch_lines = ["## Architecture Overview", ""]
    if evidence.architecture_components:
        arch_lines.append("The project follows a modular, decoupled architecture:")
        arch_lines.append("")
        for comp in evidence.architecture_components:
            tech_s = f" ({', '.join(comp.technologies)})" if comp.technologies else ""
            ep_s = f" - Entrypoint: `{comp.entrypoint}`" if comp.entrypoint else ""
            arch_lines.append(f"- **{comp.name}**{tech_s}: {comp.role}.{ep_s}")
        arch_lines.append("")

        diagram = generate_mermaid_diagram(evidence)
        if diagram:
            arch_lines.append("### Component Interaction Map")
            arch_lines.append(diagram)
            arch_lines.append("")

    if evidence.relationships:
        arch_lines.append("### Execution & Data Flow")
        for i, rel in enumerate(evidence.relationships, 1):
            arch_lines.append(
                f"{i}. **{rel.source} ➔ {rel.target}** ({rel.relationship_type}): {rel.description}"
            )
        arch_lines.append("")

    sections["architecture"] = "\n".join(arch_lines).strip()

    # 4. Tech Stack Table
    tech_lines = [
        "## Technology Stack",
        "",
        "| Layer / Role | Technologies | Description |",
        "| :--- | :--- | :--- |",
    ]
    if evidence.frameworks:
        tech_lines.append(
            f"| **Frameworks** | {', '.join(evidence.frameworks)} | Application runtimes and UI |"
        )
    if evidence.primary_language:
        tech_lines.append(
            f"| **Languages** | {', '.join(evidence.languages.keys())} | Implementation languages |"
        )
    if evidence.database_technologies:
        tech_lines.append(
            f"| **Persistence** | {', '.join(evidence.database_technologies)} | Storage & ORM |"
        )
    if evidence.background_workers:
        tech_lines.append(
            f"| **Background Tasks** | {', '.join(evidence.background_workers)} | Task queues |"
        )
    if evidence.services:
        tech_lines.append(
            "| **Infrastructure** | Docker, Docker Compose | Containerization and local runtime |"
        )

    sections["tech_stack"] = "\n".join(tech_lines).strip()

    # 5. Prerequisites
    prereq_lines = [
        "## Prerequisites",
        "",
        "Before running the project locally, verify you have installed:",
    ]
    if "Python" in evidence.languages:
        prereq_lines.append("- **Python**: `>= 3.12` recommended")
    if "TypeScript" in evidence.languages or "JavaScript" in evidence.languages:
        prereq_lines.append("- **Node.js**: `>= 20.9.0` (LTS)")
        pm = evidence.package_managers[0] if evidence.package_managers else "npm"
        prereq_lines.append(f"- **Package Manager**: `{pm}`")
    if "Go" in evidence.languages:
        prereq_lines.append("- **Go**: `>= 1.22`")
    if "Rust" in evidence.languages:
        prereq_lines.append("- **Rust / Cargo**: Latest stable toolchain")
    if evidence.services or any(c.category == "docker" for c in evidence.commands):
        prereq_lines.append("- **Docker & Docker Compose**: Compose V2 compatible runtime")
    if len(prereq_lines) == 3:
        prereq_lines.append("- **Git**: For version control and workspace management")

    sections["prerequisites"] = "\n".join(prereq_lines).strip()

    # 6. Installation
    install_lines = [
        "## Installation",
        "",
        "1. **Clone the repository:**",
        "```bash",
        f"git clone https://github.com/<owner>/{name}.git",
        f"cd {name}",
        "```",
        "",
    ]
    install_cmds = [c for c in evidence.commands if c.category == "install"]
    if install_cmds:
        install_lines.append("2. **Install project dependencies:**")
        for cmd in install_cmds:
            wd = f" (in `{cmd.working_dir}`)" if cmd.working_dir != "." else ""
            install_lines.append(f"```bash{wd}\n{cmd.command}\n```")
    else:
        install_lines.append(
            "2. **Install dependencies:** Review project manifests for installation commands."
        )

    sections["installation"] = "\n".join(install_lines).strip()

    # 7. Configuration (.env)
    config_lines = ["## Configuration", ""]
    if evidence.environment_variables:
        config_lines.append("Create a local `.env` configuration file from the template:")
        config_lines.append("```bash")
        config_lines.append("cp .env.example .env")
        config_lines.append("```")
        config_lines.append("")
        config_lines.append("| Variable | Required | Purpose | Default / Example |")
        config_lines.append("| :--- | :---: | :--- | :--- |")
        for ev in evidence.environment_variables[:15]:
            req_str = "Yes" if ev.required else "No"
            val_str = f"`{ev.example_value}`" if ev.example_value else "—"
            config_lines.append(f"| `{ev.name}` | {req_str} | {ev.purpose} | {val_str} |")
    else:
        config_lines.append(
            "No environment variables required. Check codebase for configuration defaults."
        )

    sections["configuration"] = "\n".join(config_lines).strip()

    # 8. Running the Application
    run_lines = ["## Running the Application", ""]
    docker_cmds = [c for c in evidence.commands if c.category == "docker"]
    if docker_cmds:
        run_lines.append("### Option A: Docker Compose (Recommended)")
        run_lines.append("Bring up the full development stack with a single command:")
        run_lines.append("```bash")
        run_lines.append(docker_cmds[0].command)
        run_lines.append("```")
        if evidence.services:
            run_lines.append("")
            run_lines.append("Running services:")
            for s in evidence.services:
                ports_s = f" (Ports: {', '.join(s.ports)})" if s.ports else ""
                run_lines.append(f"- **{s.name}**{ports_s}")
        run_lines.append("")

    dev_cmds = [c for c in evidence.commands if c.category == "run_dev"]
    if dev_cmds:
        run_lines.append("### Option B: Local Development")
        for c in dev_cmds:
            wd_s = f" (in `{c.working_dir}`)" if c.working_dir != "." else ""
            run_lines.append(f"- **{c.description}**{wd_s}:")
            run_lines.append(f"```bash\n{c.command}\n```")

    sections["running"] = "\n".join(run_lines).strip()

    # 9. API Reference
    api_lines = ["## API Reference", ""]
    if evidence.endpoints:
        api_lines.append("The application exposes the following verified endpoints:")
        api_lines.append("")
        api_lines.append("| Method | Path | Summary | Auth Required |")
        api_lines.append("| :---: | :--- | :--- | :---: |")
        for ep in evidence.endpoints[:12]:
            auth_s = "🔒 Yes" if ep.auth_required else "No"
            api_lines.append(f"| `{ep.method}` | `{ep.path}` | {ep.summary} | {auth_s} |")
        api_lines.append("")
        api_lines.append(
            "When running locally, visit interactive OpenAPI docs at `http://localhost:8000/docs`."
        )
    else:
        api_lines.append(
            "Interactive API documentation is available at `/docs` when the API server is active."
        )

    sections["api_reference"] = "\n".join(api_lines).strip()

    # 10. Testing & Quality Checks
    test_lines = ["## Testing & Quality", ""]
    if evidence.tests.test_commands:
        test_lines.append("Execute the automated test suites using:")
        for tc in evidence.tests.test_commands:
            test_lines.append(f"```bash\n{tc.command}\n```")
        test_lines.append("")
    if evidence.tests.test_dirs:
        dirs_str = ", ".join([f"`{d}`" for d in evidence.tests.test_dirs])
        test_lines.append(f"**Test Directories:** {dirs_str}")
    if evidence.tests.has_integration_tests:
        test_lines.append("- Integration tests verified in codebase.")
    if evidence.tests.has_e2e_tests:
        test_lines.append("- End-to-end / smoke tests verified in codebase.")

    sections["testing"] = "\n".join(test_lines).strip()

    # 11. Troubleshooting
    trouble_lines = ["## Troubleshooting", ""]
    if evidence.troubleshooting_hints:
        for hint in evidence.troubleshooting_hints:
            trouble_lines.append(f"### {hint['problem']}")
            trouble_lines.append(f"- **Cause:** {hint['cause']}")
            trouble_lines.append(f"- **Resolution:** {hint['solution']}")
            trouble_lines.append("")
    else:
        trouble_lines.append(
            "If encountering issues, inspect logs with `docker compose logs`."
        )

    sections["troubleshooting"] = "\n".join(trouble_lines).strip()

    # 12. License & Contributing
    lic_lines = ["## Contributing & License", ""]
    lic_lines.append(f"Distributed under the **{evidence.license_type or 'MIT'} License**.")
    if evidence.existing_docs:
        docs_str = ", ".join([f"`{d}`" for d in evidence.existing_docs])
        lic_lines.append(f"Refer to {docs_str} for contributing protocols.")

    sections["license"] = "\n".join(lic_lines).strip()

    # Filter by detail level
    if detail_level == "minimal":
        return {
            "overview": sections["overview"],
            "prerequisites": sections["prerequisites"],
            "installation": sections["installation"],
            "running": sections["running"],
            "testing": sections["testing"],
            "license": sections["license"],
        }
    if detail_level == "standard":
        return {
            "overview": sections["overview"],
            "features": sections["features"],
            "architecture": sections["architecture"],
            "prerequisites": sections["prerequisites"],
            "installation": sections["installation"],
            "configuration": sections["configuration"],
            "running": sections["running"],
            "testing": sections["testing"],
            "license": sections["license"],
        }

    return sections


def assemble_readme(sections: dict[str, str]) -> str:
    """Join sections into a cohesive Markdown document."""
    return "\n\n---\n\n".join(sections.values())
