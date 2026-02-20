// PropelAuth middleware — protects all routes except public ones.
// Unauthenticated users are redirected to the PropelAuth login page.
import { authMiddleware } from "@propelauth/nextjs/server/app-router";

export const middleware = authMiddleware;

export const config = {
  // Protect all routes except:
  // - static assets (_next/static, _next/image, favicon.ico)
  // - PropelAuth API callbacks (api/auth)
  // - Public pages (signup, accept-invitation)
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/auth|signup|accept-invitation).*)",
  ],
};
