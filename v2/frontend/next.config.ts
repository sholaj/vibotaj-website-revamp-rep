import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  /* config options here */
};

export default withSentryConfig(nextConfig, {
  // Suppress build logs unless running in CI
  silent: !process.env.CI,

  // Delete source maps from the build output after uploading to Sentry
  sourcemaps: {
    deleteSourcemapsAfterUpload: true,
  },

  // Reduce Sentry SDK bundle size
  bundleSizeOptimizations: {
    excludeDebugStatements: true,
  },
});
