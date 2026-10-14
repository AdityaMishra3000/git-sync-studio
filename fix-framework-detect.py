import re

extract_path = "apps/api/app/readme/extract.py"
with open(extract_path, "r") as f:
    code = f.read()

new_logic = """
    if (repo_path / "package.json").exists():
        with open(repo_path / "package.json") as f:
            import contextlib

            with contextlib.suppress(Exception):
                pkg = json.load(f)
                evidence["scripts"] = pkg.get("scripts", {})
                evidence["architecture"]["framework"] = "Node.js"
                evidence["repo"]["name"] = pkg.get("name", "Project Name")

    elif (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists():
        evidence["architecture"]["framework"] = "Python"
        
    elif (repo_path / "build.gradle").exists() or (repo_path / "settings.gradle").exists():
        evidence["architecture"]["framework"] = "Java / Android (Gradle)"
        
    elif (repo_path / "pom.xml").exists():
        evidence["architecture"]["framework"] = "Java (Maven)"
        
    elif (repo_path / "CMakeLists.txt").exists():
        evidence["architecture"]["framework"] = "C++ (CMake)"
        
    elif (repo_path / "go.mod").exists():
        evidence["architecture"]["framework"] = "Go"
        
    elif (repo_path / "Cargo.toml").exists():
        evidence["architecture"]["framework"] = "Rust"
"""

code = re.sub(
    r'    if \(repo_path / "package\.json"\)\.exists\(\):.*?evidence\["architecture"\]\["framework"\] = "Python"',
    new_logic.strip(),
    code,
    flags=re.DOTALL
)

# Also fix generate_readme to handle these frameworks intelligently
generate_logic = """def generate_readme(evidence: dict) -> str:
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
    elif framework == "Java / Android (Gradle)":
        lines.append("./gradlew build")
    elif framework == "Java (Maven)":
        lines.append("mvn install")
    elif framework == "C++ (CMake)":
        lines.append("mkdir build && cd build && cmake .. && make")
    elif framework == "Go":
        lines.append("go mod download")
    elif framework == "Rust":
        lines.append("cargo build")
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

code = re.sub(
    r'def generate_readme\(evidence: dict\) -> str:.*',
    generate_logic,
    code,
    flags=re.DOTALL
)

with open(extract_path, "w") as f:
    f.write(code)

print("Framework detection enhanced.")
