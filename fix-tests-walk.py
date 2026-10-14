import re

extract_path = "apps/api/app/readme/extract.py"
with open(extract_path, "r") as f:
    code = f.read()

new_logic = """    # Detect test folders (deep scan for monorepos)
    test_names = {"tests", "test", "__tests__", "spec", "e2e"}
    import os
    for root, dirs, files in os.walk(repo_path):
        # Prune heavy/irrelevant directories to keep it fast
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", ".venv-ml", "dist", "build"}]
        for name in test_names:
            if name in dirs:
                rel = (Path(root) / name).relative_to(repo_path)
                evidence["tests"]["folder"] = str(rel)
                break
        if evidence["tests"]:
            break"""

code = re.sub(
    r'    # Detect test folders.*?                    break',
    new_logic,
    code,
    flags=re.DOTALL
)

with open(extract_path, "w") as f:
    f.write(code)

print("os.walk test detection added.")
