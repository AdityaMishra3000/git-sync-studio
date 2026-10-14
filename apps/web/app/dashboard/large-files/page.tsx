/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { HardDrive } from "lucide-react";

export default async function LargeFilesPage() {
  let objects: any[] = [];
  try {
    objects = await ApiService.getLargeObjects();
  } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
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
