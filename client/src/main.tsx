import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
//import "./App.css"; // or index.css depending on your setup
import "./index.css"; // Ensure Tailwind CSS is imported


ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
