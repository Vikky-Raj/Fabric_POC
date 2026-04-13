import { useState, useCallback } from "react";
import {
  Upload,
  FileSpreadsheet,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const STEPS = [
  "Discovery Agent — profiling data",
  "Data Pipeline — Bronze → Silver → Gold",
  "Quality Agent — checking data quality",
  "Ontology Agent — building business ontology",
  "Semantic Agent — creating semantic model",
  "KPI Agent — computing metrics",
];

interface Props {
  onComplete: () => void;
}

export default function UploadPage({ onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const handleFile = (f: File) => {
    if (f.name.endsWith(".csv")) {
      setFile(f);
      setError("");
    } else {
      setError("Please upload a CSV file.");
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  }, []);

  const upload = async () => {
    if (!file) return;
    setProcessing(true);
    setError("");
    setCurrentStep(0);

    const stepTimer = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 8000);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: form });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || "Processing failed");
      }
      clearInterval(stepTimer);
      setCurrentStep(STEPS.length);
      setDone(true);
      setTimeout(onComplete, 1200);
    } catch (e: unknown) {
      clearInterval(stepTimer);
      setError(e instanceof Error ? e.message : "Processing failed");
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileSpreadsheet className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">
            Steel Sales Intelligence
          </h1>
          <p className="text-gray-500 mt-1">
            Upload your bronze sales data to get started
          </p>
        </div>

        {!processing ? (
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition ${
                dragOver
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
              onClick={() => document.getElementById("file-input")?.click()}
            >
              <Upload className="mx-auto h-10 w-10 text-gray-400 mb-3" />
              <p className="text-sm text-gray-600">
                {file ? (
                  <span className="font-medium text-blue-600">{file.name}</span>
                ) : (
                  <>
                    Drag &amp; drop your CSV file here, or{" "}
                    <span className="text-blue-600 font-medium">browse</span>
                  </>
                )}
              </p>
              <input
                id="file-input"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) =>
                  e.target.files?.[0] && handleFile(e.target.files[0])
                }
              />
            </div>

            {error && (
              <div className="mt-4 flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" /> {error}
              </div>
            )}

            <button
              onClick={upload}
              disabled={!file}
              className="mt-5 w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Upload &amp; Process
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border shadow-sm p-6 space-y-3">
            {STEPS.map((step, i) => {
              const isDone = i < currentStep || done;
              const isActive = i === currentStep && !done;
              return (
                <div
                  key={i}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg ${isActive ? "bg-blue-50" : ""}`}
                >
                  {isDone ? (
                    <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
                  ) : isActive ? (
                    <Loader2 className="h-5 w-5 text-blue-500 animate-spin shrink-0" />
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-gray-300 shrink-0" />
                  )}
                  <span
                    className={`text-sm ${isDone ? "text-green-700" : isActive ? "text-blue-700 font-medium" : "text-gray-400"}`}
                  >
                    {step}
                  </span>
                </div>
              );
            })}

            {done && (
              <div className="mt-2 text-center text-sm text-green-600 font-medium">
                All agents completed! Loading dashboard...
              </div>
            )}

            {error && (
              <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" /> {error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
