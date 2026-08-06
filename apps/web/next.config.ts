import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const target = process.env.NORTHSTAR_API_PROXY_TARGET;
    if (!target) return [];
    return [
      { source: "/health", destination: `${target}/health` },
      { source: "/runtime", destination: `${target}/runtime` },
      {
        source: "/demo-cases/:path*",
        destination: `${target}/demo-cases/:path*`,
      },
      { source: "/demo-cases", destination: `${target}/demo-cases` },
      { source: "/cases/:path*", destination: `${target}/cases/:path*` },
      { source: "/cases", destination: `${target}/cases` },
    ];
  },
};

export default nextConfig;
