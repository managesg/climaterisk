"use client";

import { useState } from "react";
import type { AgentRunResult, Scenario } from "../lib/types";
import { api } from "../lib/api-client";
import { ScenarioControls } from "./ScenarioControls";

interface Props {
  companyId: string;
  propertyIds: string[];
}

export function AgentPanel({ companyId, propertyIds }: Props) {
  const [scenario, setScenario] = useState<Scenario>("ssp245");
  const [year, setYear] = useState(2050);
  const [result, setResult] = useState<AgentRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"physical" | "transition" | "opportunities" | "disclosure">("physical");

  const runAgent = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.agents.run({ company_id: companyId, property_ids: propertyIds, scenario, year });
      setResult(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <ScenarioControls scenario={scenario} year={year} onScenarioChange={setScenario} onYearChange={setYear} />

      <button
        onClick={runAgent}
        disabled={loading || propertyIds.length === 0}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Running assessment…" : "▶ Run AI Assessment"}
      </button>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>
      )}

      {result && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex gap-0 border-b border-gray-200 bg-gray-50">
            {(["physical", "transition", "opportunities", "disclosure"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  tab === t ? "bg-white border-b-2 border-blue-600 text-blue-700" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <div className="p-4 max-h-96 overflow-auto">
            {tab === "physical" && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-sm font-semibold">Status:</span>
                  <span className={`px-2 py-0.5 text-xs rounded ${
                    result.status === "complete" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                  }`}>{result.status}</span>
                  {result.confidence !== undefined && (
                    <span className="text-xs text-gray-500">Confidence: {(result.confidence * 100).toFixed(0)}%</span>
                  )}
                </div>
                {result.physical_risk_results && (
                  <div className="space-y-2">
                    {Object.entries(result.physical_risk_results).map(([pid, r]) => (
                      <div key={pid} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                        <span className="font-mono text-xs text-gray-600">{pid.slice(0, 12)}…</span>
                        <span className="font-bold">{typeof r.overall_score === "number" ? r.overall_score.toFixed(1) : "N/A"}/100</span>
                      </div>
                    ))}
                  </div>
                )}
                {result.data_gaps_count !== undefined && result.data_gaps_count > 0 && (
                  <p className="mt-3 text-xs text-amber-600">⚠ {result.data_gaps_count} data gaps — see disclosure appendix</p>
                )}
              </div>
            )}

            {tab === "transition" && (
              <pre className="text-xs whitespace-pre-wrap">
                {result.transition_risk
                  ? JSON.stringify(result.transition_risk, null, 2)
                  : "No transition risk analysis available. Configure ANTHROPIC_API_KEY."}
              </pre>
            )}

            {tab === "opportunities" && (
              <pre className="text-xs whitespace-pre-wrap">
                {result.opportunities
                  ? JSON.stringify(result.opportunities, null, 2)
                  : "No opportunities analysis available. Configure ANTHROPIC_API_KEY."}
              </pre>
            )}

            {tab === "disclosure" && (
              <div className="prose prose-sm max-w-none">
                {result.disclosure_draft
                  ? <pre className="text-xs whitespace-pre-wrap">{result.disclosure_draft}</pre>
                  : "No disclosure draft available."}
              </div>
            )}
          </div>

          {result.status === "pending_review" && (
            <div className="p-4 bg-amber-50 border-t border-amber-200">
              <p className="text-sm text-amber-700 font-medium">
                ⚠ Human review required (confidence below 70% or high risk detected).
                Run ID: <code className="bg-amber-100 px-1 rounded">{result.run_id}</code>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
