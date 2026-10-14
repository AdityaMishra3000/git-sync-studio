const fs = require("fs");
const path = "apps/web/app/dashboard/readme/page.tsx";

let code = fs.readFileSync(path, "utf-8");

code = code.replace(
  `import { generateReadmeAction } from "./actions";`,
  `import { generateReadmeAction, saveReadmeAction } from "./actions";`
);

code = code.replace(
  `const [result, setResult] = useState<any>(null);`,
  `const [result, setResult] = useState<any>(null);\n  const [draftContent, setDraftContent] = useState("");\n  const [saveStatus, setSaveStatus] = useState("");`
);

code = code.replace(
  `setResult(data);`,
  `setResult(data);\n      setDraftContent(data.draft);`
);

code = code.replace(
  `async function handleGenerate(e: React.FormEvent) {`,
  `async function handleSave() {
    setSaveStatus("Saving...");
    try {
      await saveReadmeAction(repoPath, draftContent);
      setSaveStatus("Saved successfully!");
      setTimeout(() => setSaveStatus(""), 3000);
    } catch (err: any) {
      if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
      setSaveStatus("Error saving.");
    }
  }

  async function handleGenerate(e: React.FormEvent) {`
);

code = code.replace(
  `<Button variant="outline" size="sm">Approve & Save</Button>`,
  `<div className="flex items-center gap-2">
    <span className="text-xs text-muted-foreground">{saveStatus}</span>
    <Button variant="outline" size="sm" onClick={handleSave}>Approve & Save</Button>
  </div>`
);

code = code.replace(
  `defaultValue={result.draft}`,
  `value={draftContent} onChange={(e) => setDraftContent(e.target.value)}`
);

fs.writeFileSync(path, code);
console.log("README page updated.");
