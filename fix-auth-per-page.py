import re

auth_path = "apps/api/app/auth/router.py"
with open(auth_path, "r") as f:
    code = f.read()

# Change per_page=15 to per_page=100
code = code.replace("per_page=15", "per_page=100")

with open(auth_path, "w") as f:
    f.write(code)

print("Auth router per_page updated.")
