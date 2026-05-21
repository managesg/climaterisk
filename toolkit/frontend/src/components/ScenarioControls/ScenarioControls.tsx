"use client";
import type { ClimateScenario, TimeHorizon } from "@/types";
import { useAppStore } from "@/lib/store";

const SCENARIOS: { value: ClimateScenario; label: string; color: string }[] = [
  { value: "SSP1-2.6", label: "SSP1-2.6 (1.5°C)", color: "border-green-500 text-green-400" },
  { value: "SSP2-4.5", label: "SSP2-4.5 (2°C)", color: "border-yellow-500 text-yellow-400" },
  { value: "SSP5-8.5", label: "SSP5-8.5 (4°C+)", color: "border-red-500 text-red-400" },
  { value: "NGFS_NET_ZERO", label: "NGFS Net Zero", color: "border-sky-500 text-sky-400" },
  { value: "NGFS_DELAYED_TRANSITION", label: "NGFS Delayed", color: "border-orange-500 text-orange-400" },
];

const HORIZONS: TimeHorizon[] = ["current", "2030", "2040", "2050"];

export default function ScenarioControls() {
  const { scenario, setScenario } = useAppStore();

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Scenario</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {SCENARIOS.map((s) => (
          <button
            key={s.value}
            onClick={() => setScenario({ ...scenario, scenario: s.value })}
            className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all ${
              scenario.scenario === s.value
                ? s.color + " bg-slate-700"
                : "border-slate-600 text-slate-400 hover:border-slate-400"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Time Horizon</p>
      <div className="flex gap-2">
        {HORIZONS.map((h) => (
          <button
            key={h}
            onClick={() => setScenario({ ...scenario, time_horizon: h })}
            className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all ${
              scenario.time_horizon === h
                ? "border-brand-600 text-brand-600 bg-brand-600/10"
                : "border-slate-600 text-slate-400 hover:border-slate-400"
            }`}
          >
            {h}
          </button>
        ))}
      </div>
      <p className="text-xs text-slate-500 mt-3">
        Source: NASA NEX-GDDP-CMIP6 (physical) · NGFS 2023 (transition)
      </p>
    </div>
  );
}
