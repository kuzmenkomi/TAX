import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { pruneExpiredLogos } from "./lib/logoCache";

// Чистим устаревшие записи logo-кэша при каждом старте
pruneExpiredLogos();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
