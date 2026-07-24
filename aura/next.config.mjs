import { spawnSync } from "node:child_process"
import withSerwistInit from "@serwist/next"

const revision =
  spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).stdout?.trim() ||
  crypto.randomUUID()

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
  additionalPrecacheEntries: [{ url: "/offline", revision }],
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  // Phase E (DO-4): standalone build traces only the deps each page needs
  // into .next/standalone, so the production image doesn't need the full
  // node_modules tree or the pnpm store copied in.
  output: "standalone",
  turbopack: {
    root: import.meta.dirname,
  },
}

export default withSerwist(nextConfig)
