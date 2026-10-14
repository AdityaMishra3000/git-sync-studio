
import Link from "next/link";
import { FolderGit2, Home, FileText, Settings, Database, Activity, HardDrive } from "lucide-react";

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
        <Link href="/dashboard/large-files" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><HardDrive className="size-4" /> Large Files</Link>
        <Link href="/dashboard/readme" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><FileText className="size-4" /> README Generator</Link>
        <Link href="/dashboard/jobs" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Activity className="size-4" /> Jobs</Link>
      </nav>
      <div className="p-4 border-t">
        <Link href="/dashboard/settings" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"><Settings className="size-4" /> Settings</Link>
      </div>
    </div>
  );
}
