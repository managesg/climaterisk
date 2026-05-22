"use client";

import type { Scenario } from "../lib/types";

const SCENARIOS: { value: Scenario; label: string; description: string }[] = [
  { value: "ssp126", label: "SSP1-2.6", description: "Low emissions / strong policy" },
  { value: "ssp245", label: "SSP2-4.5", description: "Intermediate — current policies" },
  { value: "ssp585", label: "SSP5-8.5", description: "High emissions / limited action" },
];

const YEARS = [2030, 2050, 2100] as const;

interface Props {
  scenario: Scenario;
  year: number;
  onScenarioChange: (s: Scenario) => void;
  onYearChange: (y: number) => void;
}

export function ScenarioControls({ scenario, year, onScenarioChange, onYearChange }: Props) {
  return (
    <div className="flex flex-wrap gap-4 items-center p-3 bg-blue-50 rounded-lg border border-blue-200">
      <div>
        <label className="text-xs font-semibold text-blue-700 block mb-1">SCENARIO</label>
        <div className="flex gap-2">
          {SCENARIOS.map((s) => (
            <button
              key={s.value}
              onClick={() => onScenarioChange(s.value)}
              title={s.description}
              className={`px-3 py-1 text-sm rounded border transition-colors ${
                scenario === s.value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-blue-700 border-blue-300 hover:bg-blue-100"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-xs font-semibold text-blue-700 block mb-1">TIME HORIZON</label>
        <div className="flex gap-2">
          {YEARS.map((y) => (
            <button
              key={y}
              onClick={() => onYearChange(y)}
              className={`px-3 py-1 text-sm rounded border transition-colors ${
                year === y
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-blue-700 border-blue-300 hover:bg-blue-100"
              }`}
            >
              {y}
            </button>
          ))}
        </div>
      </div>
      <div className="text-xs text-blue-600 italic">
        Source: NASA NEX-GDDP-CMIP6 (Scenario data)
      </div>
    </div>
  );
}
