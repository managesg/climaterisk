"use client";

import { useState, useEffect } from "react";
import { AgentPanel } from "../../components/AgentPanel";
import { api } from "../../lib/api-client";
import type { Company, Property } from "../../lib/types";

export default function AgentPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProps, setSelectedProps] = useState<string[]>([]);

  useEffect(() => {
    api.companies.list().then(setCompanies).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      api.properties.list(selectedCompany.company_id).then(setProperties).catch(console.error);
      setSelectedProps([]);
    }
  }, [selectedCompany]);

  const toggleProp = (id: string) => {
    setSelectedProps((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">AI Assessment Agent</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div>
          <label className="text-sm font-semibold text-gray-600 block mb-2">Company</label>
          <select
            className="w-full border rounded p-2 text-sm"
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
          <label className="text-sm font-semibold text-gray-600 block mb-2">
            Properties {selectedProps.length > 0 && `(${selectedProps.length} selected)`}
          </label>
          <div className="border rounded p-2 max-h-32 overflow-y-auto space-y-1">
            {properties.length === 0 && (
              <p className="text-gray-400 text-sm italic">Select a company first.</p>
            )}
            {properties.map((p) => (
              <label key={p.property_id} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedProps.includes(p.property_id)}
                  onChange={() => toggleProp(p.property_id)}
                />
                {p.name} <span className="text-gray-400 text-xs">({p.asset_type})</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {selectedCompany && (
        <AgentPanel
          companyId={selectedCompany.company_id}
          propertyIds={selectedProps}
        />
      )}
    </div>
  );
}
