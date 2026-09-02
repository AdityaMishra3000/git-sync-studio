import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // `@gitsync/shared-types` ships raw TypeScript from the npm workspace, so
  // Next has to compile it rather than treat it as a prebuilt dependency.
  transpilePackages: ["@gitsync/shared-types"],

  // Monorepo: trace dependencies from the repository root so the standalone
  // build picks up workspace packages hoisted to the root node_modules.
  // Next always runs with the app directory as cwd.
  outputFileTracingRoot: path.resolve(process.cwd(), "..", ".."),
  output: "standalone",

  // Do not advertise the framework to the internet.
  poweredByHeader: false,
};

export default nextConfig;
