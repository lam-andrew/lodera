import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { APP_TITLE } from "./config/branding";

// Drive the browser tab title from the single branding source (the static title in
// index.html is only a pre-hydration fallback).
document.title = APP_TITLE;

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
