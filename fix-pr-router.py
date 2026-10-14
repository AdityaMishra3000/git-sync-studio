import re

router_path = "apps/api/app/repos/router.py"
with open(router_path, "r") as f:
    code = f.read()

code = code.replace("pr.state", "pr.status")

with open(router_path, "w") as f:
    f.write(code)

print("Fixed pr.state to pr.status")
