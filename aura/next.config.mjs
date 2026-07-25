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

export default nextConfig
