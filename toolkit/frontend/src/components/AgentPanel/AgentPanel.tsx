"use client";
import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { api } from "@/lib/api";
import type { AgentRun } from "@/types";

const STEP_LABELS: Record<string, string> = {
  validate_request: "Validate request",
  load_company: "Load company",
  load_properties: "Load properties",
  geocode_or_validate_coordinates: "Validate coordinates",
  enrich_building_context: "Enrich building context",
  score_physical_risk: "Score physical risk",
  run_transition_risk_agent: "Transition risk analysis",
  run_climate_opportunities_agent: "Climate opportunities",
  run_nature_risk_agent: "Nature risk (TNFD LEAP)",
  validate_evidence: "Validate evidence",
  check_confidence: "Check confidence",
  generate_disclosure_summary: "Generate disclosure",
};

function StateChip({ state }: { state: AgentRun["state"] }) {
  const map: Record<AgentRun["state"], string> = {
    pending: "bg-slate-700 text-slate-300",
    running: "bg-blue-700/30 text-blue-300 animate-pulse",
    awaiting_human_review: "bg-amber-700/30 text-amber-300",
    completed: "bg-green-700/30 text-green-300",
    failed: "bg-red-700/30 text-red-300",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${map[state]}`}>
      {state.replace(/_/g, " ")}
    </span>
  );
}

export default function AgentPanel() {
  const { selectedCompany, selectedProperties, scenario, activeRun, setActiveRun } = useAppStore();
  const [polling, setPolling] = useState(false);

  const startRun = async () => {
    if (!selectedCompany || selectedProperties.length === 0) return;
    try {
      const result = await api.startAssessment({
        company_id: selectedCompany.company_id,
        property_ids: selectedProperties.map((p) => p.property_id),
        task_type: "full_assessment",
        scenario: scenario.scenario,
        time_horizon: scenario.time_horizon,
      }) as { run_id: string; state: string };
      const run = await api.getRun(result.run_id) as AgentRun;
      setActiveRun(run);
      setPolling(true);
    } catch (e) {
      console.error("Failed to start assessment:", e);
    }
  };

  useEffect(() => {
    if (!polling || !activeRun) return;
    const id = setInterval(async () => {
      const run = await api.getRun(activeRun.run_id) as AgentRun;
      setActiveRun(run);
      if (run.state === "completed" || run.state === "failed" || run.state === "awaiting_human_review") {
        setPolling(false);
      }
    }, 2000);
    return () => clearInterval(id);
  }, [polling, activeRun, setActiveRun]);

  const approve = async () => {
    if (!activeRun) return;
    try {
      await api.submitReview({ run_id: activeRun.run_id, approved: true, reviewer: "user" });
      const updated = await api.getRun(activeRun.run_id) as AgentRun;
      setActiveRun(updated);
    } catch (e) {
      console.error("Review failed:", e);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-200">AI Agent</h3>
        {activeRun && <StateChip state={activeRun.state} />}
      </div>

      {/* Launch button */}
      <button
        onClick={startRun}
        disabled={!selectedCompany || selectedProperties.length === 0 || polling}
        className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg transition-all"
      >
        {polling ? "Running assessment..." : "Run Full Assessment"}
      </button>

      {(!selectedCompany || selectedProperties.length === 0) && (
        <p className="text-xs text-slate-500 text-center">
          Select a company and at least one property to run.
        </p>
      )}

      {/* Workflow progress */}
      {activeRun && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Workflow</p>
          {Object.entries(STEP_LABELS).map(([key, label]) => {
            const done = activeRun.workflow_steps_completed?.includes(key);
            return (
              <div key={key} className="flex items-center gap-2 text-xs">
                <span className={done ? "text-green-400" : "text-slate-600"}>
                  {done ? "✓" : "○"}
                </span>
                <span className={done ? "text-slate-300" : "text-slate-500"}>{label}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Confidence */}
      {activeRun?.confidence !== undefined && (
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-slate-400">Confidence</p>
          <p className={`text-2xl font-bold ${activeRun.confidence >= 0.7 ? "text-green-400" : "text-amber-400"}`}>
            {(activeRun.confidence * 100).toFixed(0)}%
          </p>
          {activeRun.confidence < 0.7 && (
            <p className="text-xs text-amber-400 mt-1">Below threshold — human review required</p>
          )}
        </div>
      )}

      {/* Human review */}
      {activeRun?.state === "awaiting_human_review" && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3 space-y-2">
          <p className="text-sm font-semibold text-amber-300">Human Review Required</p>
          {activeRun.flags?.map((f, i) => (
            <p key={i} className="text-xs text-amber-200">{f}</p>
          ))}
          <div className="flex gap-2 mt-2">
            <button
              onClick={approve}
              className="flex-1 py-1.5 bg-green-700 hover:bg-green-600 text-white text-xs font-semibold rounded-lg"
            >
              Approve
            </button>
            <button
              className="flex-1 py-1.5 bg-red-700/60 hover:bg-red-700 text-white text-xs font-semibold rounded-lg"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {activeRun?.state === "failed" && activeRun.error && (
        <div className="bg-red-900/20 border border-red-700/40 rounded-lg p-3">
          <p className="text-xs font-semibold text-red-400">Error</p>
          <p className="text-xs text-red-300 mt-1">{activeRun.error}</p>
        </div>
      )}

      {/* AI label */}
      <p className="text-xs text-slate-500 italic">
        AI outputs are labelled as ai_generated. All sources and data gaps disclosed per ISSB S2.
      </p>
    </div>
  );
}
