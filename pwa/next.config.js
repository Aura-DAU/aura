/** @type {import('next').NextConfig} */
const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
});

const nextConfig = {
  // Explicitly tell Next.js to accept the Turbopack default without warning
  turbopack: {},
};

module.exports = withPWA(nextConfig);