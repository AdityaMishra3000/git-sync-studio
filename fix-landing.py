# Fix the .env file
with open(".env", "r") as f:
    env = f.read()

env = env.replace("GITHUB_APP_CLIENT_ID=dummy_client_id", "GITHUB_APP_CLIENT_ID=Ov23liupwktyKKdJ1Tp3")
env = env.replace("GITHUB_APP_CLIENT_SECRET=dummy_client_secret", "GITHUB_APP_CLIENT_SECRET=39fa56f68c4c59f6aff7ec22261eaecb5cfa01c9")

with open(".env", "w") as f:
    f.write(env)

# Fix the landing page
landing_page_path = "apps/web/app/page.tsx"
with open(landing_page_path, "r") as f:
    landing = f.read()

# Replace the Card mapping block
old_card = """            <Card key={title} className="group hover:shadow-md transition-all hover:border-primary/50 overflow-hidden">
              <CardHeader className="relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500">
                  <Icon className="w-24 h-24" aria-hidden />
                </div>
                <Icon className="size-6 text-primary mb-2" aria-hidden />
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="font-mono text-xs text-muted-foreground">{phase}</span>
              </CardContent>
            </Card>"""

new_card = """            <Card key={title} className="group flex flex-col h-full hover:shadow-md transition-all hover:border-primary/50 overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500 pointer-events-none">
                <Icon className="w-32 h-32 -mr-6 -mt-6" aria-hidden />
              </div>
              <CardHeader className="flex-1">
                <Icon className="size-6 text-primary mb-2" aria-hidden />
                <CardTitle className="text-xl">{title}</CardTitle>
                <CardDescription className="text-sm leading-relaxed">{description}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto pt-0">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary/50 text-secondary-foreground">
                  {phase}
                </div>
              </CardContent>
            </Card>"""

landing = landing.replace(old_card, new_card)

with open(landing_page_path, "w") as f:
    f.write(landing)

print("Fixes applied.")
