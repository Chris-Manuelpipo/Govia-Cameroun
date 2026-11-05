/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Produit le serveur autonome copié par le Dockerfile.
  output: "standalone",
};

module.exports = nextConfig;
