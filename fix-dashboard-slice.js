const fs = require("fs");
const p = "apps/web/app/dashboard/page.tsx";
let code = fs.readFileSync(p, "utf-8");
code = code.replace("repos.slice(0, 5).map", "repos.map");
fs.writeFileSync(p, code);
