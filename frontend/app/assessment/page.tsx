"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "../../lib/api-client";
import type { Company, RiskAssessment } from "../../lib/types";

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

export default function AssessmentListPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);

  useEffect(() => {
    api.companies.list().then(setCompanies).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      api.assessments.list({ company_id: selectedCompany.company_id })
        .then(setAssessments)
        .catch(console.error);
    }
  }, [selectedCompany]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Risk Scorecards</h1>

      <div className="mb-6">
        <label className="block text-xs font-semibold text-gray-500 mb-1">Company</label>
        <select
          className="border rounded px-3 py-2 text-sm bg-white"
          onChange={(e) => {
            const co = companies.find((c) => c.company_id === e.target.value);
            setSelectedCompany(co ?? null);
          }}
          defaultValue=""
        >
          <option value="" disabled>Select company…</option>
          {companies.map((c) => (
            <option key={c.company_id} value={c.company_id}>{c.name}</option>
          ))}
        </select>
      </div>

      {assessments.length > 0 && (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Assessment ID</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Scenario</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Horizon</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Score</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Rating</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Confidence</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {assessments.map((a) => (
                <tr key={a.assessment_id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">{a.assessment_id.slice(0, 8)}…</td>
                  <td className="px-3 py-2">{a.scenario}</td>
                  <td className="px-3 py-2 text-right">{a.time_horizon}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {a.overall_score?.toFixed(1) ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    {a.overall_rating ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${RATING_COLORS[a.overall_rating]}`}>
                        {RATING_LABELS[a.overall_rating]}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right text-xs">
                    {(a.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-2">
                    <Link
                      href={`/assessment/${a.assessment_id}`}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!selectedCompany && (
        <div className="text-center py-16 text-gray-400 italic">Select a company to view its assessments.</div>
      )}
      {selectedCompany && assessments.length === 0 && (
        <div className="text-center py-16 text-gray-400 italic">
          No assessments found.{" "}
          <Link href="/properties" className="text-blue-600 hover:underline">Run one from the Properties page.</Link>
        </div>
      )}
    </div>
  );
}
