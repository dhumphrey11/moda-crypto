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
    // Note: rewrites() don't work with output: 'export'
    // API calls should be made directly to NEXT_PUBLIC_BACKEND_URL
}

module.exports = nextConfig