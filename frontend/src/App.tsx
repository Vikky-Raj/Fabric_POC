import { useState, useEffect } from "react";
import {
  MessageSquare,
  BarChart3,
  Network,
  ShieldCheck,
  Upload,
} from "lucide-react";
import UploadPage from "./components/UploadPage";
import ChatCopilot from "./components/ChatCopilot";
import KPIDashboard from "./components/KPIDashboard";
import OntologyView from "./components/OntologyView";
import DataQuality from "./components/DataQuality";

type Page = "chat" | "dashboard" | "ontology" | "quality";

const NAV_ITEMS: { key: Page; label: string; icon: typeof MessageSquare }[] = [
  { key: "dashboard", label: "Dashboard", icon: BarChart3 },
  { key: "ontology", label: "Ontology", icon: Network },
  { key: "quality", label: "Data Quality", icon: ShieldCheck },
  { key: "chat", label: "Chat Copilot", icon: MessageSquare },
];

export default function App() {
  const [ready, setReady] = useState(false);
  const [page, setPage] = useState<Page>("dashboard");

  useEffect(() => {
    fetch("/api/status")
      .then((r) => r.json())
      .then((d) => setReady(d.ready))
      .catch(() => {});
  }, []);

  if (!ready) {
    return (
      <UploadPage
        onComplete={() => {
          setReady(true);
          setPage("dashboard");
        }}
      />
    );
  }

  const cls = (key: Page) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
      page === key
        ? "bg-blue-50 text-blue-700"
        : "text-gray-600 hover:bg-gray-100"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="h-4 w-4 text-white" />
          </div>
          <h1 className="text-lg font-bold text-gray-800">
            Steel Sales Intelligence
          </h1>
        </div>
        <nav className="flex gap-1 items-center">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => setPage(item.key)}
              className={cls(item.key)}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </button>
          ))}
          <div className="w-px h-6 bg-gray-200 mx-1" />
          <button
            onClick={async () => {
              await fetch("/api/reset", { method: "POST" });
              setReady(false);
            }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition"
          >
            <Upload className="h-4 w-4" />
            Upload New File
          </button>
        </nav>
      </header>
      <main className="flex-1 overflow-auto bg-gray-50">
        {page === "dashboard" && <KPIDashboard />}
        {page === "ontology" && <OntologyView />}
        {page === "quality" && <DataQuality />}
        {page === "chat" && <ChatCopilot />}
      </main>
    </div>
  );
}
