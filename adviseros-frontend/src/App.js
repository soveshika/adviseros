import { useState } from "react";
import Dashboard from "./Dashboard";
import ClientProfileWizard from "./ClientProfileWizard";

export default function App() {
  const [page, setPage] = useState("dashboard"); // "dashboard" | "new-client"

  if (page === "new-client") {
    return <ClientProfileWizard onSuccess={() => setPage("dashboard")} />;
  }

  return <Dashboard onNewClient={() => setPage("new-client")} />;
}
