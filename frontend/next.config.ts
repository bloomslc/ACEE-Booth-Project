import type { NextConfig } from "next";

const imageSources = [
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080",
  ...(process.env.NEXT_PUBLIC_IMAGE_URLS ?? "").split(","),
]
  .map((source) => source.trim())
  .filter(Boolean)

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    agentUpgrade: "security",
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  images: {
    remotePatterns: imageSources.map((source) => {
      const { protocol, hostname, port } = new URL(source)
      return { protocol: protocol.replace(":", "") as "http" | "https", hostname, port }
    }),
  },
};

export default nextConfig;
