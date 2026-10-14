with open("apps/api/app/readme/extract.py", "r") as f:
    content = f.read()
import re
content = re.sub(
    r"try:\n\s*pkg = json.load\(f\)\n\s*evidence\[\"scripts\"\] = pkg\.get\(\"scripts\", \{\}\)\n\s*evidence\[\"architecture\"\]\[\"framework\"\] = \"Node\.js\"\n\s*except Exception:\n\s*pass",
    "import contextlib\n            with contextlib.suppress(Exception):\n                pkg = json.load(f)\n                evidence[\"scripts\"] = pkg.get(\"scripts\", {})\n                evidence[\"architecture\"][\"framework\"] = \"Node.js\"",
    content
)
with open("apps/api/app/readme/extract.py", "w") as f:
    f.write(content)
