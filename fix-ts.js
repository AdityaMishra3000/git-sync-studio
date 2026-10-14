const fs = require('fs');
const path = require('path');
const webPath = path.join(__dirname, 'apps/web');

function replaceFile(file, from, to) {
  const p = path.join(webPath, file);
  if (fs.existsSync(p)) {
    let content = fs.readFileSync(p, 'utf-8');
    content = content.replace(from, to);
    fs.writeFileSync(p, content);
  }
}

replaceFile('app/dashboard/page.tsx', 'let repos = [];', 'let repos: any[] = [];');
replaceFile('app/dashboard/repos/page.tsx', 'let repos = [];', 'let repos: any[] = [];');
replaceFile('app/dashboard/repos/[id]/page.tsx', 'let prs = [];', 'let prs: any[] = [];');

const authCode = `
import { cookies } from "next/headers";

export async function getToken() {
  const c = await cookies();
  return c.get("gitsync_token")?.value;
}

export async function setToken(token: string) {
  const c = await cookies();
  c.set("gitsync_token", token, { path: "/", httpOnly: true });
}

export async function clearToken() {
  const c = await cookies();
  c.delete("gitsync_token");
}
`;
fs.writeFileSync(path.join(webPath, 'lib/auth.ts'), authCode);
