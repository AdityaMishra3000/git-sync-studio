import re

extract_path = "apps/api/app/readme/extract.py"
with open(extract_path, "r") as f:
    code = f.read()

new_logic = """def generate_readme(evidence: dict) -> str:
    repo_name = evidence.get("repo", {}).get("name", "Project Name")
    lines = [
        f"# {repo_name}",
        "",
        "Welcome to the project! This README is auto-generated based on detected repository evidence.",
        "",
        "## Overview",
    ]

    framework = evidence.get("architecture", {}).get("framework")
    if framework:
        lines.append(f"This repository is primarily built with **{framework}**.")
    else:
        lines.append("This repository contains various source files.")
    
    lines.append("")
    lines.append("## Setup & Installation")
    lines.append("To get started with this project, clone the repository and install the dependencies:")
    lines.append("```bash")
    if framework == "Node.js":
        lines.append("npm install")
    elif framework == "Python":
        lines.append("pip install -r requirements.txt")
    else:
        lines.append("# Setup instructions here")
    lines.append("```")
    lines.append("")

    scripts = evidence.get("scripts", {})
    if scripts:
        lines.append("## Available Commands")
        lines.append("You can run the following scripts:")
        for k, v in scripts.items():
            lines.append(f"- `npm run {k}`: `{v}`")
        lines.append("")

    tests = evidence.get("tests", {})
    if tests:
        lines.append("## Testing")
        lines.append(f"Tests have been detected in the repository.")
        if "folder" in tests:
            lines.append(f"- **Test Directory:** `{tests['folder']}`")
        if "file" in tests:
            lines.append(f"- **Test File:** `{tests['file']}`")
        lines.append("")

    lines.append("## Architecture & Structure")
    lines.append("Review the codebase to understand its architectural decisions.")
    
    return "\\n".join(lines)
"""

# Replace the old generate_readme
code = re.sub(
    r'def generate_readme\(evidence: dict\) -> str:.*',
    new_logic,
    code,
    flags=re.DOTALL
)

with open(extract_path, "w") as f:
    f.write(code)

print("Template updated.")
