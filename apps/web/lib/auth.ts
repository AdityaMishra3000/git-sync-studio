
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
