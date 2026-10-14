const fs = require("fs");
const path = require("path");

function fixFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  let code = fs.readFileSync(filePath, "utf-8");
  
  // If it's the repo detail page
  if (code.includes("params: { id: string }") && !code.includes("await params")) {
    code = code.replace(
      "export default async function RepoDetailPage({ params }: { params: { id: string } }) {",
      "export default async function RepoDetailPage({ params }: { params: Promise<{ id: string }> }) {\n  const resolvedParams = await params;\n  const id = resolvedParams.id;"
    );
    code = code.replaceAll("params.id", "id");
    fs.writeFileSync(filePath, code);
    console.log("Fixed " + filePath);
  }

  // If it's the PR detail page
  if (code.includes("params: { id: string; prId: string }") && !code.includes("await params")) {
    code = code.replace(
      "export default async function PrPredictionPage({ params }: { params: { id: string; prId: string } }) {",
      "export default async function PrPredictionPage({ params }: { params: Promise<{ id: string; prId: string }> }) {\n  const resolvedParams = await params;\n  const { id, prId } = resolvedParams;"
    );
    code = code.replaceAll("params.id", "id").replaceAll("params.prId", "prId");
    fs.writeFileSync(filePath, code);
    console.log("Fixed " + filePath);
  }
}

fixFile("apps/web/app/dashboard/repos/[id]/page.tsx");
fixFile("apps/web/app/dashboard/repos/[id]/pr/[prId]/page.tsx");
