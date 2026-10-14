import os

extract_path = "apps/api/app/readme/extract.py"
with open(extract_path, "r") as f:
    code = f.read()

# Add test folder detection
new_logic = """    if (repo_path / "pyproject.toml").exists():
        evidence["architecture"]["framework"] = "Python"

    # Detect test folders
    test_folders = ["tests", "test", "__tests__", "spec", "e2e"]
    for folder in test_folders:
        if (repo_path / folder).is_dir():
            evidence["tests"]["folder"] = folder
            break"""

code = code.replace(
    'if (repo_path / "pyproject.toml").exists():\n        evidence["architecture"]["framework"] = "Python"',
    new_logic
)

with open(extract_path, "w") as f:
    f.write(code)

print("Tests detection logic added.")
