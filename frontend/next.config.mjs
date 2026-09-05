/** @type {import('next').NextConfig} */

const nextConfig = {
  output: process.env.VERCEL ? undefined : "standalone",
  reactStrictMode: true,
};

export default nextConfig;