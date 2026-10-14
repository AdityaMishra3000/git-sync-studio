# Fix docker-compose.yaml
compose_path = "compose.yaml"
with open(compose_path, "r") as f:
    compose = f.read()

# Add the host home directory to backend mounts
if "- /home/adityam:/home/adityam" not in compose:
    compose = compose.replace(
        "  - ./apps/worker:/srv/worker",
        "  - ./apps/worker:/srv/worker\n  - /home/adityam:/home/adityam"
    )

with open(compose_path, "w") as f:
    f.write(compose)

# Remove the fallback hack from readme/router.py
router_path = "apps/api/app/readme/router.py"
with open(router_path, "r") as f:
    router = f.read()

router = router.replace(
    'if not path.exists():  # noqa: ASYNC240\n        # Fallback to analyzing the API source itself for demo purposes\n        path = Path("/srv/api")',
    'if not path.exists():  # noqa: ASYNC240\n        raise HTTPException(status_code=404, detail="Repo path not found in container")'
)

with open(router_path, "w") as f:
    f.write(router)

print("Mounts updated and fallback removed.")
