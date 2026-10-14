
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
    const res = await fetch(`${serverApiBaseUrl()}/api/v1/auth/github/callback?code=${code}`, { cache: "no-store" });
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
