import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";
import { postJSON } from "../api/client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

interface Message {
  role: "user" | "assistant";
  content: string;
  chart_data?: ChartData | null;
}

interface ChartData {
  type: "bar" | "line" | "pie";
  title: string;
  data: { label: string; value: number }[];
}

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
];

const SUGGESTED = [
  "What is the total revenue by region?",
  "Which customers are repeat buyers?",
  "Average selling price by product?",
  "Which region contributes the highest revenue?",
  "Show me the ontology entities",
];

export default function ChatCopilot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");
    const userMsg: Message = { role: "user", content: msg };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await postJSON<{ response: string; chart_data?: ChartData }>(
        "/api/chat",
        { message: msg },
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.response,
          chart_data: res.chart_data,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error connecting to the API. Is the backend running?",
        },
      ]);
    }
    setLoading(false);
  };

  const renderChart = (chart: ChartData) => {
    if (chart.type === "pie") {
      return (
        <div className="mt-3 bg-white rounded-lg p-4 border">
          <p className="text-sm font-medium text-gray-700 mb-2">
            {chart.title}
          </p>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chart.data}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {chart.data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }
    return (
      <div className="mt-3 bg-white rounded-lg p-4 border">
        <p className="text-sm font-medium text-gray-700 mb-2">{chart.title}</p>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chart.data}>
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-16">
            <Bot className="mx-auto h-12 w-12 text-blue-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Steel Sales Intelligence Copilot
            </h2>
            <p className="text-gray-500 mb-6">
              Ask questions about your sales data
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}
          >
            {m.role === "assistant" && (
              <Bot className="h-6 w-6 text-blue-500 mt-1 shrink-0" />
            )}
            <div
              className={`max-w-[75%] rounded-lg px-4 py-3 ${
                m.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-200"
              }`}
            >
              <p className="whitespace-pre-wrap text-sm">{m.content}</p>
              {m.chart_data && renderChart(m.chart_data)}
            </div>
            {m.role === "user" && (
              <User className="h-6 w-6 text-gray-400 mt-1 shrink-0" />
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <Bot className="h-6 w-6 text-blue-500 mt-1" />
            <div className="bg-white border rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-white p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2 max-w-3xl mx-auto"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your sales data..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
