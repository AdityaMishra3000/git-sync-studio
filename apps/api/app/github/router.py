import hashlib
import hmac
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_db_session
from app.db.models import GitHubInstallation

router = APIRouter(prefix="/github", tags=["github"])


def get_github_jwt() -> str:
    settings = get_settings()
    now = int(datetime.now(UTC).timestamp())
    payload = {"iat": now, "exp": now + (10 * 60), "iss": settings.github_app_id}
    if not settings.github_private_key:
        raise ValueError("GitHub private key not configured")
    return jwt.encode(payload, settings.github_private_key.get_secret_value(), algorithm="RS256")


async def verify_webhook_signature(request: Request) -> bytes:
    settings = get_settings()
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    secret = settings.github_webhook_secret.get_secret_value().encode()
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature_header, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return body


@router.post("/webhooks")
async def github_webhook(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> dict[str, str]:
    await verify_webhook_signature(request)
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    if event_type == "installation":
        action = payload.get("action")
        installation_id = payload["installation"]["id"]
        target_id = payload["installation"]["account"]["id"]
        target_type = payload["installation"]["account"]["type"]

        if action == "created":
            result = await session.execute(
                select(GitHubInstallation).where(
                    GitHubInstallation.installation_id == installation_id
                )
            )
            inst = result.scalar_one_or_none()
            if not inst:
                inst = GitHubInstallation(
                    installation_id=installation_id, target_id=target_id, target_type=target_type
                )
                session.add(inst)
                await session.commit()
        elif action == "deleted":
            result = await session.execute(
                select(GitHubInstallation).where(
                    GitHubInstallation.installation_id == installation_id
                )
            )
            inst = result.scalar_one_or_none()
            if inst:
                await session.delete(inst)
                await session.commit()
    return {"status": "accepted"}
