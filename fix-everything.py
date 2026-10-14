import os
import glob
import re

# 1. Fix NEXT_REDIRECT in all dashboard pages and login page
for root, dirs, files in os.walk("apps/web/app"):
    for file in files:
        if file.endswith(".tsx") or file.endswith(".ts"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            # Replace catch blocks
            if "catch (err" in content:
                content = re.sub(
                    r'catch\s*\(\s*err(?:\s*:\s*any)?\s*\)\s*{',
                    r'catch (err: any) {\n    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;',
                    content
                )
                with open(path, "w") as f:
                    f.write(content)

# 2. Mock GitHub OAuth
auth_router_path = "apps/api/app/auth/router.py"
with open(auth_router_path, "r") as f:
    auth_router = f.read()

# Add mock login
auth_router = auth_router.replace(
    'if not settings.github_client_id:',
    '''if settings.github_client_id == "dummy_client_id":
        return {"url": "http://localhost:3100/auth/callback?code=mock_code"}
    if not settings.github_client_id:'''
)

# Add mock callback
mock_callback = '''    if code == "mock_code":
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
        return {"access_token": token, "token_type": "bearer"}

    settings = get_settings()'''

auth_router = auth_router.replace(
    'settings = get_settings()\n    async with httpx.AsyncClient() as client:',
    mock_callback + '\n    async with httpx.AsyncClient() as client:'
)

with open(auth_router_path, "w") as f:
    f.write(auth_router)

# 3. Enhance landing page
landing_page_path = "apps/web/app/page.tsx"
with open(landing_page_path, "r") as f:
    landing = f.read()

# Make it more appealing with Tailwind animations and modern layout
new_landing = landing.replace(
    '<div className="flex flex-col gap-10">',
    '<div className="flex flex-col gap-16 min-h-screen bg-gradient-to-b from-background to-muted/20 pb-20">'
).replace(
    '<section className="flex flex-col gap-4">',
    '<section className="flex flex-col gap-6 items-center text-center pt-24 pb-12 px-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 fill-mode-both">',
    1 # Only the first section (hero)
).replace(
    '<p className="font-mono text-xs tracking-widest text-muted-foreground uppercase">',
    '<div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 animate-in fade-in zoom-in duration-700 delay-200 fill-mode-both">🚀 Phase 0 · Foundation</div>\n        <p className="font-mono text-xs tracking-widest text-muted-foreground uppercase sr-only">'
).replace(
    '<h1 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">',
    '<h1 className="font-heading text-5xl font-extrabold tracking-tight sm:text-6xl md:text-7xl bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">'
).replace(
    '<p className="max-w-2xl text-base text-muted-foreground">',
    '<p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">'
).replace(
    '<div className="flex flex-wrap gap-3">',
    '<div className="flex flex-wrap gap-4 justify-center mt-6 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300 fill-mode-both">'
).replace(
    '<Button asChild>',
    '<Button asChild size="lg" className="rounded-full px-8 shadow-lg hover:shadow-xl transition-all">'
).replace(
    '<section className="flex flex-col gap-4">',
    '<section className="flex flex-col gap-8 px-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500 fill-mode-both">'
).replace(
    '<Card key={title}>',
    '<Card key={title} className="group hover:shadow-md transition-all hover:border-primary/50 overflow-hidden">'
).replace(
    '<CardHeader>',
    '<CardHeader className="relative overflow-hidden">\n                <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500">\n                  <Icon className="w-24 h-24" aria-hidden />\n                </div>'
).replace(
    '<Icon className="size-4 text-muted-foreground" aria-hidden />',
    '<Icon className="size-6 text-primary mb-2" aria-hidden />'
)

with open(landing_page_path, "w") as f:
    f.write(new_landing)

print("All fixes applied successfully.")
