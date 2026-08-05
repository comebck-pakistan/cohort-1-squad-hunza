/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['images.unsplash.com', 'lh3.googleusercontent.com', 'wanvhvtdpynebwlvorpw.supabase.co'],
  },
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  webpack: (config, { dev }) => {
    if (dev) {
      // Disable Webpack disk caching to prevent memory allocation crashes
      config.cache = false;
    }
    return config;
  },
};

module.exports = nextConfig;