import { useEffect, useState } from "react";
import { fetchJSON } from "../api/client";
import { CheckCircle, XCircle, Shield } from "lucide-react";

interface RuleCheck {
  rule: string;
  passed: boolean;
  detail: string;
}

interface AIAnalysis {
  overall_status: string;
  score: number;
  narrative: string;
  findings: {
    rule: string;
    status: string;
    severity: string;
    explanation: string;
    recommendation: string;
  }[];
  risks: string[];
  recommendations: string[];
}

interface QualityData {
  rule_based_checks: {
    total: number;
    passed: number;
    failed: number;
    rules: RuleCheck[];
  };
  ai_analysis: AIAnalysis;
}

export default function DataQuality() {
  const [data, setData] = useState<QualityData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJSON<QualityData>("/api/quality")
      .then(setData)
      .catch(() =>
        setError("Failed to load quality report. Run the pipeline first."),
      );
  }, []);

  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!data)
    return (
      <div className="p-8 text-center text-gray-500">
        Loading quality report...
      </div>
    );

  const { rule_based_checks: rules, ai_analysis: ai } = data;
  const scoreColor =
    ai.score >= 80
      ? "text-green-600"
      : ai.score >= 50
        ? "text-amber-600"
        : "text-red-600";

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800">Data Quality Report</h1>

      {/* Score Card */}
      <div className="flex items-center gap-6 bg-white border rounded-xl p-6">
        <div className="text-center">
          <p className={`text-5xl font-bold ${scoreColor}`}>{ai.score}</p>
          <p className="text-sm text-gray-500 mt-1">Quality Score</p>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Shield className={`h-5 w-5 ${scoreColor}`} />
            <span className="font-semibold capitalize text-gray-700">
              {ai.overall_status}
            </span>
            <span className="text-sm text-gray-400">
              — {rules.passed}/{rules.total} rules passed
            </span>
          </div>
          <p className="text-sm text-gray-600">{ai.narrative}</p>
        </div>
      </div>

      {/* Rule Results */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">
          Quality Rules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rules.rules.map((r, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 bg-white border rounded-lg p-4 ${r.passed ? "" : "border-red-300 bg-red-50"}`}
            >
              {r.passed ? (
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
              )}
              <div>
                <p className="font-medium text-gray-800">{r.rule}</p>
                <p className="text-sm text-gray-500">{r.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Findings */}
      {ai.findings && ai.findings.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            AI Findings
          </h2>
          <div className="space-y-2">
            {ai.findings.map((f, i) => (
              <div key={i} className="bg-white border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded ${
                      f.severity === "critical"
                        ? "bg-red-100 text-red-700"
                        : f.severity === "warning"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {f.severity}
                  </span>
                  <span className="font-medium text-gray-800">{f.rule}</span>
                </div>
                <p className="text-sm text-gray-600">{f.explanation}</p>
                <p className="text-sm text-blue-600 mt-1">
                  → {f.recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risks & Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ai.risks && ai.risks.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <h3 className="font-semibold text-red-800 mb-2">Risks</h3>
            <ul className="space-y-1">
              {ai.risks.map((r, i) => (
                <li key={i} className="text-sm text-red-700">
                  • {r}
                </li>
              ))}
            </ul>
          </div>
        )}
        {ai.recommendations && ai.recommendations.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-5">
            <h3 className="font-semibold text-green-800 mb-2">
              Recommendations
            </h3>
            <ul className="space-y-1">
              {ai.recommendations.map((r, i) => (
                <li key={i} className="text-sm text-green-700">
                  • {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
