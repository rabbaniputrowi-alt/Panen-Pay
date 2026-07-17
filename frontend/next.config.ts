import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root: a stray lockfile above this repo otherwise makes
  // Turbopack guess the wrong root.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
