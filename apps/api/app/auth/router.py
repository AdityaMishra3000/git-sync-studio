from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, get_current_user
from app.core.config import get_settings
from app.core.dependencies import get_db_session
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.get("/github/login")
async def github_login():
    settings = get_settings()
    if settings.github_client_id == "dummy_client_id":
        return {"url": "http://localhost:3100/auth/callback?code=mock_code"}
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
    url = f"https://github.com/login/oauth/authorize?client_id={settings.github_client_id}&scope=user:email,repo"
    return {"url": url}


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(code: str, session: AsyncSession = Depends(get_db_session)):
    if code == "mock_code":
        primary_email = "mock@example.com"
        name = "Demo User"
        result = await session.execute(select(User).where(User.email == primary_email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email=primary_email, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        token = create_access_token(user.id, timedelta(days=7))

        # Fetch and sync repos
        repos_resp = await client.get(
            "https://api.github.com/user/repos?per_page=100",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()
            from app.db.models import Repository
            for r in repos_data:
                repo_result = await session.execute(select(Repository).where(Repository.github_repo_id == r["id"]))
                if not repo_result.scalar_one_or_none():
                    new_repo = Repository(
                        github_repo_id=r["id"],
                        owner=r["owner"]["login"],
                        name=r["name"],
                        default_branch=r.get("default_branch", "main"),
                        visibility="private" if r.get("private") else "public",
                        sync_status="synced"
                    )
                    session.add(new_repo)
            await session.commit()

        return {"access_token": token, "token_type": "bearer"}

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret.get_secret_value()
                if settings.github_client_secret
                else "",
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Invalid code")

        user_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        emails = user_resp.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)
        if not primary_email:
            raise HTTPException(status_code=400, detail="Primary email required")

        profile_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        profile = profile_resp.json()
        name = profile.get("name") or profile.get("login")

        result = await session.execute(select(User).where(User.email == primary_email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email=primary_email, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        token = create_access_token(user.id, timedelta(days=7))

        # Fetch and sync repos
        repos_resp = await client.get(
            "https://api.github.com/user/repos?per_page=100",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()
            from app.db.models import Repository
            for r in repos_data:
                repo_result = await session.execute(select(Repository).where(Repository.github_repo_id == r["id"]))
                if not repo_result.scalar_one_or_none():
                    new_repo = Repository(
                        github_repo_id=r["id"],
                        owner=r["owner"]["login"],
                        name=r["name"],
                        default_branch=r.get("default_branch", "main"),
                        visibility="private" if r.get("private") else "public",
                        sync_status="synced"
                    )
                    session.add(new_repo)
            await session.commit()

        return {"access_token": token, "token_type": "bearer"}


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "name": user.name}
