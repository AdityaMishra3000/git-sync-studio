import os

config_path = "apps/api/app/core/config.py"
with open(config_path, "r") as f:
    config = f.read()

config = config.replace(
    "github_app_id: str | None = None",
    'github_app_id: str | None = Field(default=None, validation_alias="GITHUB_APP_ID")'
).replace(
    "github_client_id: str | None = None",
    'github_client_id: str | None = Field(default=None, validation_alias="GITHUB_APP_CLIENT_ID")'
).replace(
    "github_client_secret: SecretStr | None = None",
    'github_client_secret: SecretStr | None = Field(default=None, validation_alias="GITHUB_APP_CLIENT_SECRET")'
)

if "from pydantic import" in config and "Field" not in config:
    config = config.replace("from pydantic import SecretStr, field_validator", "from pydantic import SecretStr, field_validator, Field")

with open(config_path, "w") as f:
    f.write(config)

server_api_client_path = "apps/web/lib/server-api-client.ts"
with open(server_api_client_path, "r") as f:
    client = f.read()

if 'import { redirect }' not in client:
    client = 'import { redirect } from "next/navigation";\n' + client

client = client.replace(
    "if (!res.ok) {",
    """if (!res.ok) {
    if (res.status === 401) {
      redirect("/login");
    }"""
)

with open(server_api_client_path, "w") as f:
    f.write(client)

# Fix .env
with open(".env", "r") as f:
    env = f.read()

env = env.replace("GITHUB_APP_CLIENT_ID=", "GITHUB_APP_CLIENT_ID=dummy_client_id")
env = env.replace("GITHUB_APP_CLIENT_SECRET=", "GITHUB_APP_CLIENT_SECRET=dummy_client_secret")

with open(".env", "w") as f:
    f.write(env)

print("Fixes applied.")
