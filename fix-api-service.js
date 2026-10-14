const fs = require("fs");
const p = "apps/web/lib/api-service.ts";
let code = fs.readFileSync(p, "utf-8");
code = code.replace(
  "getPrediction: (prId: string): Promise<any> => fetchServerApi(`/api/v1/prediction/${prId}`, { cache: \"no-store\" }),",
  "getPrediction: (prId: string): Promise<any> => fetchServerApi(`/api/v1/prediction/${prId}`, { cache: \"no-store\" }),\n  getJobs: (): Promise<any[]> => fetchServerApi(\"/api/v1/jobs\", { cache: \"no-store\" }),"
);
fs.writeFileSync(p, code);
