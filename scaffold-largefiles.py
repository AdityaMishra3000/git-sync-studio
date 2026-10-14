import os

web_path = "apps/web"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# Update ApiService
api_service = os.path.join(web_path, "lib/api-service.ts")
with open(api_service, "r") as f:
    code = f.read()
if "getLargeObjects:" not in code:
    code = code.replace("getPrs: (repoId: string): Promise<any[]> => fetchApi(`/api/v1/repos/${repoId}/prs`, { cache: \"no-store\" }),", "getPrs: (repoId: string): Promise<any[]> => fetchApi(`/api/v1/repos/${repoId}/prs`, { cache: \"no-store\" }),\n  getLargeObjects: (): Promise<any[]> => fetchApi(`/api/v1/drive`, { cache: \"no-store\" }),")
    with open(api_service, "w") as f:
        f.write(code)

# Sidebar update
sidebar_path = os.path.join(web_path, "components/layout/sidebar.tsx")
with open(sidebar_path, "r") as f:
    sidebar = f.read()
if "/dashboard/large-files" not in sidebar:
    sidebar = sidebar.replace('import { FolderGit2, Home, FileText, Settings, Database, Activity } from "lucide-react";', 'import { FolderGit2, Home, FileText, Settings, Database, Activity, HardDrive } from "lucide-react";')
    sidebar = sidebar.replace('<Link href="/dashboard/readme" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><FileText className="size-4" /> README Generator</Link>', '<Link href="/dashboard/large-files" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><HardDrive className="size-4" /> Large Files</Link>\n        <Link href="/dashboard/readme" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><FileText className="size-4" /> README Generator</Link>')
    with open(sidebar_path, "w") as f:
        f.write(sidebar)

# Large Files Page
write_file(os.path.join(web_path, "app/dashboard/large-files/page.tsx"), """
import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { HardDrive } from "lucide-react";

export default async function LargeFilesPage() {
  let objects: any[] = [];
  try {
    objects = await ApiService.getLargeObjects();
  } catch (err) {
    console.error(err);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Large Files</h1>
        <p className="text-muted-foreground mt-2">Drive-backed binary object tracking.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><HardDrive className="h-5 w-5" /> Objects Registry</CardTitle>
          <CardDescription>All files uploaded and replaced with Git pointers.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Path</th>
                <th className="px-4 py-3 font-medium">Size (Bytes)</th>
                <th className="px-4 py-3 font-medium">SHA-256 OID</th>
                <th className="px-4 py-3 font-medium">Drive Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {objects.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    No large files found.
                  </td>
                </tr>
              )}
              {objects.map((obj) => (
                <tr key={obj.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{obj.path}</td>
                  <td className="px-4 py-3">{obj.size_bytes}</td>
                  <td className="px-4 py-3 font-mono text-xs">{obj.oid.substring(0, 16)}...</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${obj.drive_status === 'synced' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>
                      {obj.drive_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
""")

print("Large Files scaffolded.")
