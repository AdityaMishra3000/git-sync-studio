import re

auth_path = "apps/api/app/auth/router.py"
with open(auth_path, "r") as f:
    code = f.read()

# Fix the scope
code = code.replace(
    'scope=user:email',
    'scope=user:email,repo'
)

# Inject repo fetching logic
repo_fetch_logic = """        token = create_access_token(user.id, timedelta(days=7))

        # Fetch and sync repos
        repos_resp = await client.get(
            "https://api.github.com/user/repos?per_page=15",
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

        return {"access_token": token, "token_type": "bearer"}"""

code = code.replace(
    '        token = create_access_token(user.id, timedelta(days=7))\n        return {"access_token": token, "token_type": "bearer"}',
    repo_fetch_logic
)

with open(auth_path, "w") as f:
    f.write(code)

print("Auth router patched with repo sync logic.")
