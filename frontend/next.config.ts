import path from "node:path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

loadEnvConfig(path.resolve(process.cwd(), ".."));

const nextConfig: NextConfig = { reactStrictMode: true, output: "standalone" };
export default nextConfig;
