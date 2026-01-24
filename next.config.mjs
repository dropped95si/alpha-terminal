/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // !! WARN !!
    // This allows production builds to complete even if
    // your project has type errors from the new JSON data.
    ignoreBuildErrors: true,
  },
  eslint: {
    // This allows production builds to complete even if
    // your project has linting errors.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;