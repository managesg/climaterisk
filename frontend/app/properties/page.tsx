"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { PropertyTable } from "../../components/PropertyTable";
import { api } from "../../lib/api-client";
import type { Company, Property, RiskAssessment, Scenario } from "../../lib/types";

const SCENARIOS: { value: Scenario; label: string }[] = [
  { value: "ssp126", label: "SSP1-2.6 (Low)" },
  { value: "ssp245", label: "SSP2-4.5 (Medium)" },
  { value: "ssp585", label: "SSP5-8.5 (High)" },
];

const HORIZONS = [2030, 2050, 2100];

const RATING_COLORS: Record<string, string> = {
  very_low: "bg-green-100 text-green-800",
  low: "bg-lime-100 text-lime-800",
  moderate: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  very_high: "bg-red-100 text-red-800",
};

const RATING_LABELS: Record<string, string> = {
  very_low: "Very Low", low: "Low", moderate: "Moderate",
  high: "High", very_high: "Very High",
};

export default function PropertiesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [scenario, setScenario] = useState<Scenario>("ssp245");
  const [horizon, setHorizon] = useState(2050);
  const [running, setRunning] = useState(false);
  const [selectedPropIds, setSelectedPropIds] = useState<string[]>([]);

  useEffect(() => {
    api.companies.list().then(setCompanies).catch(console.error);
  }, []);

  const loadProperties = useCallback((cid: string) => {
    api.properties.list(cid).then(setProperties).catch(console.error);
    api.assessments.list({ company_id: cid }).then(setAssessments).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedCompany) loadProperties(selectedCompany.company_id);
  }, [selectedCompany, loadProperties]);

  const latestAssessment = (propId: string): RiskAssessment | undefined =>
    assessments
      .filter((a) => a.property_id === propId && a.scenario === scenario && a.time_horizon === horizon)
      .sort((a, b) => b.created_at.localeCompare(a.created_at))[0];

  const toggleProp = (id: string) =>
    setSelectedPropIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );

  const runAssessments = async () => {
    if (!selectedCompany || selectedPropIds.length === 0) return;
    setRunning(true);
    try {
      await api.assessments.run({
        company_id: selectedCompany.company_id,
        property_ids: selectedPropIds,
        scenario,
        time_horizon: horizon,
      });
      loadProperties(selectedCompany.company_id);
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Asset Portfolio</h1>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-6 items-end">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Company</label>
          <select
            className="border rounded px-3 py-2 text-sm bg-white"
            onChange={(e) => {
              const co = companies.find((c) => c.company_id === e.target.value);
              setSelectedCompany(co ?? null);
              setSelectedPropIds([]);
            }}
            defaultValue=""
          >
            <option value="" disabled>Select company…</option>
            {companies.map((c) => (
              <option key={c.company_id} value={c.company_id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Scenario</label>
          <div className="flex gap-1">
            {SCENARIOS.map((s) => (
              <button
                key={s.value}
                onClick={() => setScenario(s.value)}
                className={`px-3 py-2 rounded text-xs font-medium border transition-colors ${
                  scenario === s.value
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Time Horizon</label>
          <div className="flex gap-1">
            {HORIZONS.map((y) => (
              <button
                key={y}
                onClick={() => setHorizon(y)}
                className={`px-3 py-2 rounded text-xs font-medium border transition-colors ${
                  horizon === y
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {y}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Property grid */}
      {properties.length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden mb-6">
          <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">
              {properties.length} properties
            </span>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">
                {selectedPropIds.length > 0 ? `${selectedPropIds.length} selected` : "Select to run"}
              </span>
              <button
                onClick={runAssessments}
                disabled={running || selectedPropIds.length === 0}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-medium disabled:opacity-50 hover:bg-blue-700 transition-colors"
              >
                {running ? "Running…" : "Run Assessment"}
              </button>
            </div>
          </div>

          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-8 px-3 py-2" />
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Name</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Type</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Location</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Score</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Rating</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-600">Scorecard</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {properties.map((p) => {
                const a = latestAssessment(p.property_id);
                return (
                  <tr key={p.property_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedPropIds.includes(p.property_id)}
                        onChange={() => toggleProp(p.property_id)}
                      />
                    </td>
                    <td className="px-3 py-2 font-medium">{p.name}</td>
                    <td className="px-3 py-2 capitalize text-gray-600">{p.asset_type}</td>
                    <td className="px-3 py-2 text-gray-600">{p.city}, {p.state}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {a ? a.overall_score?.toFixed(1) : "—"}
                    </td>
                    <td className="px-3 py-2">
                      {a?.overall_rating ? (
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${RATING_COLORS[a.overall_rating]}`}>
                          {RATING_LABELS[a.overall_rating]}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs italic">not run</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {a ? (
                        <Link
                          href={`/assessment/${a.assessment_id}`}
                          className="text-blue-600 hover:underline text-xs"
                        >
                          View →
                        </Link>
                      ) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!selectedCompany && (
        <div className="text-center py-16 text-gray-400 italic">
          Select a company to view its portfolio.
        </div>
      )}
      {selectedCompany && properties.length === 0 && (
        <div className="text-center py-16 text-gray-400 italic">
          No properties found for this company.
        </div>
      )}
    </div>
  );
}
