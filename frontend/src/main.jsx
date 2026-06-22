import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles.css";

// Global fetch interceptor to inject authentication keys automatically
const originalFetch = window.fetch;
window.fetch = async function (url, options = {}) {
  const key = localStorage.getItem("nexus_cre_api_key") || import.meta.env.VITE_API_KEY || "";
  if (
    key &&
    typeof url === "string" &&
    (url.startsWith("/") ||
      url.startsWith("http://localhost:") ||
      url.includes(import.meta.env.VITE_API_URL || "") ||
      url.includes("/ingest") ||
      url.includes("/chat") ||
      url.includes("/explain") ||
      url.includes("/reports") ||
      url.includes("/report/"))
  ) {
    if (!options.headers) {
      options.headers = {};
    }
    if (options.headers instanceof Headers) {
      options.headers.set("X-API-Key", key);
      options.headers.set("Authorization", `Bearer ${key}`);
    } else {
      options.headers["X-API-Key"] = key;
      options.headers["Authorization"] = `Bearer ${key}`;
    }
  }
  return originalFetch(url, options);
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
