import path from "path";
import { fileURLToPath } from "url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    proxy: {
      // All /api requests → FastAPI backend on port 8000
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (id.includes("@metamask/sdk")) {
            return "wallet-metamask";
          }
          if (id.includes("@walletconnect") || id.includes("@reown")) {
            return "walletconnect";
          }
          if (id.includes("@coinbase/wallet-sdk")) {
            return "wallet-coinbase";
          }
          if (id.includes("recharts") || id.includes("d3-") || id.includes("internmap")) {
            return "charts";
          }
          return undefined;
        },
      },
    },
  },
});
