import { useEffect, useState } from "react";
import { fetchJSON } from "../api/client";
import { TrendingUp, Users, DollarSign, MapPin } from "lucide-react";
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

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

interface KPIData {
  metrics: {
    total_revenue: number;
    total_volume_tons: number;
    order_count: number;
    customer_count: number;
  };
  kpis: {
    average_selling_price: number;
    regional_contribution: Record<string, number>;
    customer_retention_rate: number;
  };
  top_customer: { name: string; revenue: number };
  revenue_by_region: Record<string, number>;
  revenue_by_product: Record<string, number>;
  ai_analysis?: {
    interpretation: string;
    highlights: { metric: string; insight: string }[];
  };
}

export default function KPIDashboard() {
  const [data, setData] = useState<KPIData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJSON<KPIData>("/api/kpis")
      .then(setData)
      .catch(() => setError("Failed to load KPIs. Run the pipeline first."));
  }, []);

  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!data)
    return <div className="p-8 text-center text-gray-500">Loading KPIs...</div>;

  const regionData = Object.entries(data.revenue_by_region).map(
    ([label, value]) => ({ label, value }),
  );
  const productData = Object.entries(data.revenue_by_product).map(
    ([label, value]) => ({ label, value }),
  );

  const cards = [
    {
      icon: DollarSign,
      label: "Total Revenue",
      value: `₹${data.metrics.total_revenue.toLocaleString()}`,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      icon: TrendingUp,
      label: "Avg Selling Price",
      value: `₹${data.kpis.average_selling_price.toLocaleString()}`,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      icon: Users,
      label: "Customer Retention",
      value: `${data.kpis.customer_retention_rate}%`,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      icon: MapPin,
      label: "Top Customer",
      value: data.top_customer.name,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800">
        Sales Intelligence Dashboard
      </h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div
            key={c.label}
            className="bg-white rounded-xl border p-5 flex items-start gap-4"
          >
            <div className={`p-2 rounded-lg ${c.bg}`}>
              <c.icon className={`h-5 w-5 ${c.color}`} />
            </div>
            <div>
              <p className="text-sm text-gray-500">{c.label}</p>
              <p className="text-xl font-semibold text-gray-800">{c.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">
            Revenue by Region
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={regionData}>
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => `₹${v.toLocaleString()}`} />
              <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">
            Revenue by Product
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={productData}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ label, percent }) =>
                  `${label} (${(percent * 100).toFixed(0)}%)`
                }
              >
                {productData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => `₹${v.toLocaleString()}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Regional Contribution */}
      <div className="bg-white rounded-xl border p-5">
        <h3 className="font-semibold text-gray-700 mb-4">
          Regional Sales Contribution
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(data.kpis.regional_contribution).map(
            ([region, pct]) => (
              <div
                key={region}
                className="text-center p-3 bg-gray-50 rounded-lg"
              >
                <p className="text-2xl font-bold text-blue-600">{pct}%</p>
                <p className="text-sm text-gray-500">{region}</p>
              </div>
            ),
          )}
        </div>
      </div>

      {/* AI Interpretation */}
      {data.ai_analysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h3 className="font-semibold text-blue-800 mb-2">AI Analysis</h3>
          <p className="text-sm text-blue-900 whitespace-pre-wrap">
            {data.ai_analysis.interpretation}
          </p>
          {data.ai_analysis.highlights && (
            <div className="mt-3 space-y-1">
              {data.ai_analysis.highlights.map((h, i) => (
                <p key={i} className="text-sm">
                  <span className="font-medium text-blue-800">{h.metric}:</span>{" "}
                  {h.insight}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
