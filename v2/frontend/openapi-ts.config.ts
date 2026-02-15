import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: process.env.OPENAPI_URL || "http://localhost:8000/openapi.json",
  output: {
    format: "prettier",
    lint: "eslint",
    path: "src/lib/api/generated",
  },
  plugins: [
    {
      enums: "javascript",
      name: "@hey-api/typescript",
    },
    "@hey-api/schemas",
    {
      name: "@hey-api/sdk",
      operationId: true,
    },
    "@hey-api/client-fetch",
    "@tanstack/react-query",
  ],
});
