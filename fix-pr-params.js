const fs = require("fs");
const filePath = "apps/web/app/dashboard/repos/[id]/pr/[prId]/page.tsx";
let code = fs.readFileSync(filePath, "utf-8");

code = code.replace(
  "export default async function PrPredictionPage({ params }: { params: { id: string, prId: string } }) {",
  "export default async function PrPredictionPage({ params }: { params: Promise<{ id: string, prId: string }> }) {\n  const resolvedParams = await params;\n  const { id, prId } = resolvedParams;"
);
code = code.replaceAll("params.prId", "prId").replaceAll("params.id", "id");

fs.writeFileSync(filePath, code);
console.log("Fixed PR params");
