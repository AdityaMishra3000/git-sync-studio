import re
with open("apps/api/app/auth/router.py", "r") as f:
    code = f.read()

code = code.replace(
"""        if code == "mock_code":
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
        return {"access_token": token, "token_type": "bearer"}""",
"""    if code == "mock_code":
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
        return {"access_token": token, "token_type": "bearer"}"""
)
with open("apps/api/app/auth/router.py", "w") as f:
    f.write(code)
