import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  cacheOnFrontEndNav: true,
  // Cache static assets only, NO API caching (per CLAUDE.md guidelines)
  publicExcludes: ["!ncache/**/*"],
  fallbacks: {
    document: "/offline", // redirect here when offline and not cached
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {

  images: {
    unoptimized: true,
  },
  turbopack: {},
}

export default withPWA(nextConfig);
