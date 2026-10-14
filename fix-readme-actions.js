const fs = require("fs");
const path = "apps/web/app/dashboard/readme/actions.ts";

let code = fs.readFileSync(path, "utf-8");

if (!code.includes("saveReadmeAction")) {
  code += `\n
export async function saveReadmeAction(repoPath: string, content: string) {
  return fetchServerApi("/api/v1/readme/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath, content }),
  });
}
`;
  fs.writeFileSync(path, code);
}
console.log("actions.ts updated.");
