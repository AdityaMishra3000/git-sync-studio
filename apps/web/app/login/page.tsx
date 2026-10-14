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
  } catch (err: unknown) {
    if ((err as { digest?: string })?.digest?.startsWith("NEXT_REDIRECT")) throw err;
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
          <CardDescription>
            Connect your GitHub account to start analyzing repositories and generating documentation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action={handleLogin}>
            <Button type="submit" className="w-full">
              Continue with GitHub
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
