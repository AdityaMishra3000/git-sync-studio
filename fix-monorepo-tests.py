import re

extract_path = "apps/api/app/readme/extract.py"
with open(extract_path, "r") as f:
    code = f.read()

new_logic = """    # Detect test folders (root and 1-level deep for monorepos)
    test_names = {"tests", "test", "__tests__", "spec", "e2e"}
    for name in test_names:
        if (repo_path / name).is_dir():
            evidence["tests"]["folder"] = name
            break
    
    if not evidence["tests"]:
        import contextlib
        with contextlib.suppress(Exception):
            for item in repo_path.iterdir():
                if item.is_dir() and item.name not in {".git", "node_modules", ".venv", ".venv-ml", "dist", "build"}:
                    for name in test_names:
                        if (item / name).is_dir():
                            evidence["tests"]["folder"] = f"{item.name}/{name}"
                            break
                if evidence["tests"]:
                    break"""

code = re.sub(
    r'    # Detect test folders\n    test_folders = \["tests".*?            break',
    new_logic,
    code,
    flags=re.DOTALL
)

with open(extract_path, "w") as f:
    f.write(code)

print("Monorepo test detection added.")
