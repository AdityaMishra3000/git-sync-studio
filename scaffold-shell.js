const fs = require('fs');
const path = require('path');

const webPath = path.join(__dirname, 'apps/web');

// Make dirs
['app/login', 'app/auth/callback', 'app/dashboard', 'components/layout'].forEach(d => {
  fs.mkdirSync(path.join(webPath, d), { recursive: true });
});

// App Shell Components
const sidebarCode = `
import Link from "next/link";
import { FolderGit2, Home, FileText, Settings, Database, Activity } from "lucide-react";

export function Sidebar() {
  return (
    <div className="w-64 border-r bg-muted/30 flex flex-col h-screen">
      <div className="p-4 border-b font-bold text-lg flex items-center gap-2">
        <FolderGit2 className="size-5" />
        GitSync Studio
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <Link href="/dashboard" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Home className="size-4" /> Dashboard</Link>
        <Link href="/dashboard/repos" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Database className="size-4" /> Repositories</Link>
        <Link href="/dashboard/readme" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><FileText className="size-4" /> README Generator</Link>
        <Link href="/dashboard/jobs" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Activity className="size-4" /> Jobs</Link>
      </nav>
      <div className="p-4 border-t">
        <Link href="/dashboard/settings" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Settings className="size-4" /> Settings</Link>
      </div>
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'components/layout/sidebar.tsx'), sidebarCode);

const shellCode = `
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-14 border-b flex items-center px-6 bg-background">
          <div className="flex-1"></div>
          <div className="text-sm text-muted-foreground flex items-center gap-2">
             User Profile
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6 bg-muted/10">
          {children}
        </main>
      </div>
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'components/layout/app-shell.tsx'), shellCode);

// Login Page
const loginCode = `
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiService } from "@/lib/api-service";
import { FolderGit2 } from "lucide-react";
import { redirect } from "next/navigation";

export default async function LoginPage() {
  let url = "";
  try {
    const res = await ApiService.getLoginUrl();
    url = res.url;
  } catch (err) {
    console.error(err);
  }

  async function handleLogin() {
    "use server";
    redirect(url);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/20">
      <Card className="w-[400px]">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-full">
              <FolderGit2 className="size-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl">GitSync Studio</CardTitle>
          <CardDescription className="text-base mt-2">
            Repository intelligence, large-file management, and evidence-grounded documentation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action={handleLogin}>
            <Button className="w-full" size="lg" disabled={!url}>
              Continue with GitHub
            </Button>
          </form>
          {!url && <p className="text-destructive text-sm text-center mt-2">Backend connection failed.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'app/login/page.tsx'), loginCode);

// Auth Callback Route
const callbackCode = `
import { serverApiBaseUrl } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { redirect } from "next/navigation";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  
  if (!code) {
    return new Response("Missing code", { status: 400 });
  }

  try {
    const res = await fetch(\`\${serverApiBaseUrl()}/api/v1/auth/github/callback?code=\${code}\`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("Failed to auth");
    }
    const data = await res.json();
    await setToken(data.access_token);
  } catch (error) {
    console.error(error);
    return new Response("Auth failed", { status: 500 });
  }

  redirect("/dashboard");
}
`;
fs.writeFileSync(path.join(webPath, 'app/auth/callback/route.ts'), callbackCode);

// Update root layout to skip shell, let dashboard layout handle shell
const layoutCode = `
import "./globals.css";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'app/layout.tsx'), layoutCode);

const dashLayoutCode = `
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/layout.tsx'), dashLayoutCode);

console.log("Shell scaffolded.");
