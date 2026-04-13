import { useEffect, useState } from "react";
import { fetchJSON } from "../api/client";
import { ArrowRight } from "lucide-react";

interface Entity {
  "@type": string;
  description?: string;
  properties?:
    | { name: string; data_type?: string; description?: string }[]
    | string[];
}

interface Relationship {
  subject: string;
  predicate: string;
  object: string;
  description?: string;
}

interface GlossaryItem {
  term: string;
  definition: string;
  related_entity?: string;
}

interface Ontology {
  ontology_name?: string;
  description?: string;
  entities: Entity[];
  relationships: Relationship[];
  business_glossary?: GlossaryItem[];
}

const ENTITY_COLORS: Record<string, string> = {
  Customer: "bg-blue-100 border-blue-300 text-blue-800",
  Product: "bg-green-100 border-green-300 text-green-800",
  SalesOrder: "bg-amber-100 border-amber-300 text-amber-800",
  Region: "bg-purple-100 border-purple-300 text-purple-800",
  TimePeriod: "bg-pink-100 border-pink-300 text-pink-800",
};

export default function OntologyView() {
  const [data, setData] = useState<Ontology | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJSON<Ontology>("/api/ontology")
      .then(setData)
      .catch(() =>
        setError("Failed to load ontology. Run the pipeline first."),
      );
  }, []);

  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!data)
    return (
      <div className="p-8 text-center text-gray-500">Loading ontology...</div>
    );

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">
          {data.ontology_name || "Business Ontology"}
        </h1>
        {data.description && (
          <p className="text-gray-500 mt-1">{data.description}</p>
        )}
      </div>

      {/* Entities */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Entities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.entities.map((e) => {
            const type = e["@type"];
            const colorClass =
              ENTITY_COLORS[type] ||
              "bg-gray-100 border-gray-300 text-gray-800";
            return (
              <div
                key={type}
                className={`rounded-xl border-2 p-4 ${colorClass}`}
              >
                <h3 className="font-bold text-lg">{type}</h3>
                {e.description && (
                  <p className="text-sm mt-1 opacity-80">{e.description}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-1">
                  {(e.properties || []).map((p, i) => {
                    const name = typeof p === "string" ? p : p.name;
                    return (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-white/60 rounded text-xs font-mono"
                      >
                        {name}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Relationships */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">
          Relationships
        </h2>
        <div className="space-y-2">
          {data.relationships.map((r, i) => (
            <div
              key={i}
              className="flex items-center gap-2 bg-white border rounded-lg px-4 py-3"
            >
              <span className="font-semibold text-blue-700">{r.subject}</span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
              <span className="px-2 py-0.5 bg-gray-100 rounded text-sm font-medium text-gray-600">
                {r.predicate}
              </span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
              <span className="font-semibold text-green-700">{r.object}</span>
              {r.description && (
                <span className="ml-auto text-xs text-gray-400">
                  {r.description}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Business Glossary */}
      {data.business_glossary && data.business_glossary.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            Business Glossary
          </h2>
          <div className="bg-white border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Term
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Definition
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Entity
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.business_glossary.map((g, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2 font-medium">{g.term}</td>
                    <td className="px-4 py-2 text-gray-600">{g.definition}</td>
                    <td className="px-4 py-2">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                        {g.related_entity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
