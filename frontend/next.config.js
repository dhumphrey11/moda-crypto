/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',  // Enable static exports for Firebase Hosting
    trailingSlash: true,
    images: {
        unoptimized: true,  // Disable image optimization for static export
    },
    env: {
        CUSTOM_KEY: 'my-value',
    },
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/:path*`,
            },
        ]
    },
}

module.exports = nextConfig