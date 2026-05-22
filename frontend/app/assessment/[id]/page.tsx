"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { RiskScorecard } from "../../../components/RiskScorecard";
import { api } from "../../../lib/api-client";
import type { RiskAssessment, HazardType } from "../../../lib/types";

const HAZARD_LABELS: Record<HazardType, string> = {
  wildfire: "Wildfire",
  inland_flood: "Inland Flood",
  coastal_flood: "Coastal Flood / SLR",
  heat_stress: "Heat Stress",
  drought: "Drought / Water",
  wind_hurricane: "Wind / Hurricane",
};

const DATA_TYPE_COLORS: Record<string, string> = {
  observed: "bg-blue-100 text-blue-800",
  modeled: "bg-purple-100 text-purple-800",
  scenario: "bg-indigo-100 text-indigo-800",
  ai_generated: "bg-pink-100 text-pink-800",
  user_provided: "bg-green-100 text-green-800",
  missing: "bg-gray-100 text-gray-500",
};

export default function AssessmentPage() {
  const { id } = useParams<{ id: string }>();
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [activeHazard, setActiveHazard] = useState<HazardType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.assessments.get(id)
      .then((a) => {
        setAssessment(a);
        const first = Object.keys(a.hazard_scores)[0] as HazardType | undefined;
        if (first) setActiveHazard(first);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-gray-500">Loading assessment…</div>;
  if (error || !assessment) return (
    <div className="p-8">
      <p className="text-red-600 mb-4">{error ?? "Assessment not found."}</p>
      <Link href="/properties" className="text-blue-600 hover:underline">← Back to properties</Link>
    </div>
  );

  const SCENARIO_LABELS: Record<string, string> = {
    ssp126: "SSP1-2.6 (Low emissions)",
    ssp245: "SSP2-4.5 (Medium emissions)",
    ssp585: "SSP5-8.5 (High emissions)",
  };

  const drillHazard = activeHazard ? assessment.hazard_scores[activeHazard] : null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/properties" className="text-sm text-blue-600 hover:underline">
          ← Back to portfolio
        </Link>
        <h1 className="text-2xl font-bold mt-2">Risk Scorecard</h1>
        <div className="flex gap-4 mt-1 text-sm text-gray-500">
          <span>{SCENARIO_LABELS[assessment.scenario] ?? assessment.scenario}</span>
          <span>·</span>
          <span>{assessment.time_horizon}</span>
          <span>·</span>
          <span>Confidence: {(assessment.confidence * 100).toFixed(0)}%</span>
          <span>·</span>
          <span className="text-xs text-gray-400">ID: {assessment.assessment_id.slice(0, 8)}</span>
        </div>
      </div>

      {/* Overall + per-hazard gauges */}
      <div className="mb-8">
        <RiskScorecard
          hazardScores={assessment.hazard_scores}
          overallScore={assessment.overall_score ?? undefined}
          overallRating={assessment.overall_rating ?? undefined}
        />
      </div>

      {/* Feature drill-down */}
      {Object.keys(assessment.hazard_scores).length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm mb-8">
          <div className="px-4 py-3 border-b bg-gray-50 flex gap-2 flex-wrap">
            {(Object.keys(assessment.hazard_scores) as HazardType[]).map((h) => (
              <button
                key={h}
                onClick={() => setActiveHazard(h)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  activeHazard === h
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                {HAZARD_LABELS[h]}
              </button>
            ))}
          </div>

          {drillHazard && (
            <div className="p-4">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 font-semibold">
                    <th className="pb-2 pr-3">Feature</th>
                    <th className="pb-2 pr-3 text-right">Raw Value</th>
                    <th className="pb-2 pr-3 text-right">Score /100</th>
                    <th className="pb-2 pr-3">Data Type</th>
                    <th className="pb-2 pr-3 text-right">Confidence</th>
                    <th className="pb-2">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {drillHazard.feature_scores.map((f) => (
                    <tr key={f.feature_name} className={f.is_available ? "" : "opacity-50"}>
                      <td className="py-1.5 pr-3 font-medium">{f.feature_name.replace(/_/g, " ")}</td>
                      <td className="py-1.5 pr-3 text-right font-mono text-xs">
                        {f.raw_value !== null && f.raw_value !== undefined ? String(f.raw_value) : "—"}
                      </td>
                      <td className="py-1.5 pr-3 text-right font-mono">
                        {f.normalized_score.toFixed(1)}
                      </td>
                      <td className="py-1.5 pr-3">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${DATA_TYPE_COLORS[f.data_type] ?? "bg-gray-100"}`}>
                          {f.data_type}
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 text-right text-xs">
                        {(f.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-1.5 text-xs text-gray-500">
                        {f.source_url ? (
                          <a href={f.source_url} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
                            {f.source}
                          </a>
                        ) : f.source}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {drillHazard.recommended_action && (
                <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-800">
                  <strong>Recommended action:</strong> {drillHazard.recommended_action}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Data gaps + assumptions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {assessment.data_gaps.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <h3 className="font-semibold text-amber-800 mb-2">
              Data Gaps ({assessment.data_gaps.length})
            </h3>
            <ul className="text-sm text-amber-700 space-y-1 list-disc list-inside">
              {assessment.data_gaps.map((g) => <li key={g}>{g}</li>)}
            </ul>
          </div>
        )}

        {assessment.assumptions.length > 0 && (
          <div className="bg-gray-50 border rounded-xl p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Assumptions</h3>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              {assessment.assumptions.map((a) => <li key={a}>{a}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
