import re

# apps/api/app/auth/router.py
with open("apps/api/app/auth/router.py", "r") as f:
    content = f.read()
content = content.replace(
    '"client_secret": settings.github_client_secret.get_secret_value() if settings.github_client_secret else "",',
    '"client_secret": settings.github_client_secret.get_secret_value()\n                if settings.github_client_secret else "",'
)
with open("apps/api/app/auth/router.py", "w") as f:
    f.write(content)


# apps/api/app/auth/security.py
with open("apps/api/app/auth/security.py", "r") as f:
    content = f.read()
content = content.replace(
    'async def get_current_user(session: AsyncSession = Depends(get_db_session), token: str = Depends(oauth2_scheme)) -> User:',
    'async def get_current_user(\n    session: AsyncSession = Depends(get_db_session),\n    token: str = Depends(oauth2_scheme)\n) -> User:'
)
content = content.replace(
    'except jwt.InvalidTokenError:',
    'except jwt.InvalidTokenError as err:'
)
content = content.replace(
    'detail="Could not validate credentials",\n        )',
    'detail="Could not validate credentials",\n        ) from err'
)
with open("apps/api/app/auth/security.py", "w") as f:
    f.write(content)

# apps/api/app/github/router.py
with open("apps/api/app/github/router.py", "r") as f:
    content = f.read()
content = content.replace(
    'async def github_webhook(request: Request, session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:',
    'async def github_webhook(\n    request: Request, session: AsyncSession = Depends(get_db_session)\n) -> dict[str, str]:'
)
content = content.replace(
    'select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)',
    'select(GitHubInstallation).where(\n                GitHubInstallation.installation_id == installation_id\n            )'
)
with open("apps/api/app/github/router.py", "w") as f:
    f.write(content)

