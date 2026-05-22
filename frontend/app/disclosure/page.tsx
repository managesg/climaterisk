"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "../../lib/api-client";
import type { Company, Property } from "../../lib/types";

export default function DisclosurePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedPropIds, setSelectedPropIds] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<{ run_id: string; disclosure_markdown: string; confidence: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.companies.list().then(setCompanies).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      api.properties.list(selectedCompany.company_id).then(setProperties).catch(console.error);
      setSelectedPropIds([]);
    }
  }, [selectedCompany]);

  const toggleProp = (id: string) =>
    setSelectedPropIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );

  const generate = async () => {
    if (!selectedCompany || selectedPropIds.length === 0) return;
    setGenerating(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.disclosures.generate({
        company_id: selectedCompany.company_id,
        property_ids: selectedPropIds,
        scenario: "ssp245",
        year: 2050,
      });
      setResult(r);
    } catch (e) {
      setError(String(e));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">Disclosure Report</h1>
      <p className="text-gray-500 text-sm mb-6">
        Generate an ISSB IFRS S2 / TCFD / TNFD-aligned disclosure report.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Company</label>
          <select
            className="w-full border rounded px-3 py-2 text-sm bg-white"
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

        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-gray-500 mb-1">
            Properties {selectedPropIds.length > 0 && `(${selectedPropIds.length} selected)`}
          </label>
          <div className="border rounded p-2 max-h-28 overflow-y-auto bg-white space-y-1">
            {properties.length === 0 ? (
              <p className="text-gray-400 text-xs italic">Select a company first.</p>
            ) : (
              properties.map((p) => (
                <label key={p.property_id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedPropIds.includes(p.property_id)}
                    onChange={() => toggleProp(p.property_id)}
                  />
                  {p.name}
                  <span className="text-gray-400 text-xs">({p.asset_type})</span>
                </label>
              ))
            )}
          </div>
        </div>
      </div>

      <button
        onClick={generate}
        disabled={generating || !selectedCompany || selectedPropIds.length === 0}
        className="px-6 py-2 bg-blue-600 text-white rounded font-medium disabled:opacity-50 hover:bg-blue-700 transition-colors"
      >
        {generating ? "Generating…" : "Generate Disclosure Report"}
      </button>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Generated Report</h2>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Confidence: {(result.confidence * 100).toFixed(0)}%</span>
              <span className="text-xs font-mono text-gray-400">run/{result.run_id.slice(0, 8)}</span>
            </div>
          </div>
          <div className="bg-white border rounded-xl shadow-sm p-6">
            <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800 leading-relaxed overflow-auto max-h-[70vh]">
              {result.disclosure_markdown}
            </pre>
          </div>
        </div>
      )}

      {!result && !generating && (
        <div className="mt-8 text-center py-12 text-gray-400 italic border border-dashed rounded-xl">
          Select a company and properties, then click Generate.
        </div>
      )}
    </div>
  );
}
