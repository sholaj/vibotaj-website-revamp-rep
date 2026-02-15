// PropelAuth callback route handlers.
// Handles /api/auth/login, /api/auth/callback, /api/auth/logout, etc.
import { getRouteHandlers } from "@propelauth/nextjs/server/app-router";

const routeHandlers = getRouteHandlers();

export const GET = routeHandlers.getRouteHandlerAsync;
export const POST = routeHandlers.postRouteHandlerAsync;
