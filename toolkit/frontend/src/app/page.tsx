"use client";
import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { api } from "@/lib/api";
import type { Company, Property, PhysicalRiskResult } from "@/types";
import RiskScorecard from "@/components/RiskScorecard/RiskScorecard";
import PropertyTable from "@/components/PropertyTable/PropertyTable";
import ScenarioControls from "@/components/ScenarioControls/ScenarioControls";
import AgentPanel from "@/components/AgentPanel/AgentPanel";
import ClimateMap from "@/components/Map/ClimateMap";

export default function Home() {
  const {
    selectedCompany, setSelectedCompany,
    selectedProperties, setSelectedProperties,
    riskResults, setRiskResults,
    sidebarTab, setSidebarTab,
    scenario,
  } = useAppStore();

  const [companies, setCompanies] = useState<Company[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedPropId, setSelectedPropId] = useState<string>("");
  const [screeningLoading, setScreeningLoading] = useState(false);

  useEffect(() => {
    api.getCompanies().then((cs) => setCompanies(cs as Company[])).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedCompany) return;
    api.getProperties(selectedCompany.company_id)
      .then((ps) => {
        setProperties(ps as Property[]);
        setSelectedProperties(ps as Property[]);
      })
      .catch(console.error);
  }, [selectedCompany, setSelectedProperties]);

  const runScreening = async () => {
    if (!selectedCompany || properties.length === 0) return;
    setScreeningLoading(true);
    try {
      const results: PhysicalRiskResult[] = [];
      for (const prop of properties.slice(0, 10)) {
        const r = await api.quickScreen(prop.property_id, scenario.scenario, scenario.time_horizon) as PhysicalRiskResult;
        results.push(r);
      }
      setRiskResults(results);
    } catch (e) {
      console.error("Screening error:", e);
    } finally {
      setScreeningLoading(false);
    }
  };

  const selectedResult = riskResults.find((r) => r.property_id === selectedPropId);

  return (
    <div className="flex flex-col h-screen bg-[#0f1117] overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-700 bg-slate-900 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
            SB
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100">SeaBridge AI Sustainability Toolkit</h1>
            <p className="text-xs text-slate-400">Physical Risk · Transition Risk · Nature · ISSB IFRS S2</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Company selector */}
          <select
            value={selectedCompany?.company_id || ""}
            onChange={(e) => {
              const c = companies.find((x) => x.company_id === e.target.value);
              setSelectedCompany(c || null);
            }}
            className="text-xs bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-slate-200"
          >
            <option value="">Select company...</option>
            {companies.map((c) => (
              <option key={c.company_id} value={c.company_id}>{c.name}</option>
            ))}
          </select>
          <button
            onClick={runScreening}
            disabled={screeningLoading || !selectedCompany || properties.length === 0}
            className="text-xs bg-brand-600 hover:bg-brand-700 disabled:bg-slate-700 disabled:text-slate-500 text-white px-4 py-1.5 rounded-lg font-semibold transition-all"
          >
            {screeningLoading ? "Screening..." : "Screen Portfolio"}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: map + table */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          {/* Map */}
          <div className="h-64 flex-shrink-0 p-4 pb-0">
            <ClimateMap
              properties={properties}
              riskResults={riskResults}
              selectedId={selectedPropId}
              onSelectProperty={setSelectedPropId}
            />
          </div>

          {/* Scenario controls */}
          <div className="p-4 pb-0">
            <ScenarioControls />
          </div>

          {/* Property table */}
          <div className="flex-1 overflow-auto p-4">
            <div className="bg-slate-800 rounded-xl border border-slate-700">
              <div className="px-4 py-3 border-b border-slate-700">
                <h2 className="text-sm font-semibold text-slate-200">
                  Properties {properties.length > 0 && `(${properties.length})`}
                </h2>
              </div>
              <PropertyTable
                properties={properties}
                riskResults={riskResults}
                onSelect={(p) => setSelectedPropId(p.property_id)}
                selectedId={selectedPropId}
              />
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-96 flex-shrink-0 border-l border-slate-700 flex flex-col overflow-hidden">
          {/* Sidebar tabs */}
          <div className="flex border-b border-slate-700 flex-shrink-0">
            {(["properties", "risk", "agent", "disclosure"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setSidebarTab(tab)}
                className={`flex-1 py-2.5 text-xs font-semibold capitalize transition-colors ${
                  sidebarTab === tab
                    ? "text-brand-600 border-b-2 border-brand-600"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-4">
            {sidebarTab === "risk" && (
              <>
                {selectedResult ? (
                  <RiskScorecard result={selectedResult} />
                ) : riskResults.length > 0 ? (
                  riskResults.map((r) => <RiskScorecard key={r.property_id} result={r} />)
                ) : (
                  <div className="text-center text-slate-500 py-8 text-sm">
                    Run screening to see risk scores.
                  </div>
                )}
              </>
            )}

            {sidebarTab === "agent" && <AgentPanel />}

            {sidebarTab === "disclosure" && (
              <DisclosurePanel />
            )}

            {sidebarTab === "properties" && (
              <PropertiesPanel
                selectedCompany={selectedCompany}
                onPropertyAdded={() => {
                  if (selectedCompany) {
                    api.getProperties(selectedCompany.company_id)
                      .then((ps) => setProperties(ps as Property[]))
                      .catch(console.error);
                  }
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DisclosurePanel() {
  const { activeRun } = useAppStore();
  const [disclosure, setDisclosure] = useState<Record<string, unknown> | null>(null);

  const fetch = async () => {
    if (!activeRun?.run_id) return;
    try {
      const result = await api.getDisclosure(activeRun.run_id) as { disclosure: Record<string, unknown> };
      setDisclosure(result.disclosure || null);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-3">
      <button
        onClick={fetch}
        disabled={!activeRun}
        className="w-full py-2 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg"
      >
        Load Disclosure Report
      </button>
      {!activeRun && <p className="text-xs text-slate-500 text-center">Run an agent assessment first.</p>}
      {disclosure && (
        <div className="space-y-3">
          {Object.entries(disclosure).map(([key, value]) => {
            if (key === "disclaimer") {
              return (
                <div key={key} className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3">
                  <p className="text-xs text-amber-300">{value as string}</p>
                </div>
              );
            }
            if (typeof value === "object" && value !== null && "section" in (value as Record<string, unknown>)) {
              const section = value as Record<string, unknown>;
              return (
                <div key={key} className="bg-slate-700/50 rounded-lg p-3">
                  <p className="text-xs font-bold text-slate-300 mb-2">{section.section as string}</p>
                  {section.data_source_type && (
                    <span className="text-xs bg-purple-900/40 text-purple-300 px-2 py-0.5 rounded-full">
                      {section.data_source_type as string}
                    </span>
                  )}
                  {section.narrative && (
                    <p className="text-xs text-slate-400 mt-2">{section.narrative as string}</p>
                  )}
                </div>
              );
            }
            return null;
          })}
        </div>
      )}
    </div>
  );
}

function PropertiesPanel({
  selectedCompany,
  onPropertyAdded,
}: {
  selectedCompany: Company | null;
  onPropertyAdded: () => void;
}) {
  const [form, setForm] = useState({
    name: "", latitude: "", longitude: "",
    asset_type: "Office", city: "", country: "",
    fema_flood_zone: "", elevation_m: "", distance_to_coast_km: "",
  });
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompany) return;
    setSaving(true);
    try {
      await api.createProperty({
        ...form,
        company_id: selectedCompany.company_id,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        elevation_m: form.elevation_m ? parseFloat(form.elevation_m) : undefined,
        distance_to_coast_km: form.distance_to_coast_km ? parseFloat(form.distance_to_coast_km) : undefined,
      });
      setForm({ name: "", latitude: "", longitude: "", asset_type: "Office", city: "", country: "", fema_flood_zone: "", elevation_m: "", distance_to_coast_km: "" });
      onPropertyAdded();
    } catch (e) {
      console.error("Create property failed:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {!selectedCompany && (
        <p className="text-xs text-slate-500 text-center py-4">Select a company first.</p>
      )}
      {selectedCompany && (
        <form onSubmit={submit} className="space-y-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Add Property</p>
          {[
            { field: "name", label: "Name", required: true },
            { field: "latitude", label: "Latitude", required: true },
            { field: "longitude", label: "Longitude", required: true },
            { field: "city", label: "City" },
            { field: "country", label: "Country" },
            { field: "elevation_m", label: "Elevation (m)" },
            { field: "distance_to_coast_km", label: "Distance to Coast (km)" },
            { field: "fema_flood_zone", label: "FEMA Flood Zone" },
          ].map(({ field, label, required }) => (
            <div key={field}>
              <label className="text-xs text-slate-400">{label}{required && " *"}</label>
              <input
                value={(form as Record<string, string>)[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                required={required}
                className="mt-0.5 w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-600"
              />
            </div>
          ))}
          <div>
            <label className="text-xs text-slate-400">Asset Type *</label>
            <select
              value={form.asset_type}
              onChange={(e) => setForm({ ...form, asset_type: e.target.value })}
              className="mt-0.5 w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-600"
            >
              {["Office", "Retail", "Industrial", "Residential", "Data Center", "Healthcare", "Hospitality", "Mixed Use"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="w-full py-2 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-700 text-white text-sm font-semibold rounded-lg"
          >
            {saving ? "Adding..." : "Add Property"}
          </button>
        </form>
      )}
    </div>
  );
}
