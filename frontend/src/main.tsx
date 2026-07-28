/**
 * CodeCompass — Entry Point
 *
 * Mounts the React app into the HTML page.
 * Chain: index.html → main.tsx → App.tsx → LandingPage
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
