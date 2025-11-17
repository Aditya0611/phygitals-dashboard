/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove output: 'export' to enable server-side API routes
  trailingSlash: true,
  images: {
    unoptimized: true
  }
}

module.exports = nextConfig
