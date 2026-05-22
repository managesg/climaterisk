"use client";
import type { PhysicalRiskResult, HazardResult } from "@/types";
import clsx from "clsx";

function ratingClass(rating: string) {
  const r = rating.toLowerCase().replace(" ", "-");
  return `badge-${r}`;
}

function ratingColor(score: number): string {
  if (score <= 20) return "#16a34a";
  if (score <= 40) return "#65a30d";
  if (score <= 60) return "#ca8a04";
  if (score <= 80) return "#ea580c";
  return "#dc2626";
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
      <div
        className="h-2 rounded-full transition-all"
        style={{ width: `${score}%`, background: ratingColor(score) }}
      />
    </div>
  );
}

function HazardRow({ h }: { h: HazardResult }) {
  if (!h.applicable) {
    return (
      <div className="flex items-center justify-between py-1.5 text-sm text-slate-500">
        <span>{h.hazard}</span>
        <span className="text-xs italic">N/A</span>
      </div>
    );
  }
  return (
    <div className="py-2 border-b border-slate-700/50 last:border-0">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-200">{h.hazard}</span>
        <span
          className={clsx("text-xs px-2 py-0.5 rounded-full font-semibold", ratingClass(h.rating))}
        >
          {h.rating} ({h.category_score.toFixed(0)})
        </span>
      </div>
      <ScoreBar score={h.category_score} />
      {h.top_drivers.length > 0 && (
        <p className="text-xs text-slate-400 mt-1">
          Drivers: {h.top_drivers.join(", ")}
        </p>
      )}
      {h.data_gaps.length > 0 && (
        <p className="text-xs text-amber-500 mt-0.5">
          Data gaps: {h.data_gaps.slice(0, 2).join("; ")}
        </p>
      )}
    </div>
  );
}

interface Props {
  result: PhysicalRiskResult;
}

export default function RiskScorecard({ result }: Props) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-slate-100">{result.property_name || result.property_id}</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {result.scenario} · {result.time_horizon} · Confidence: {result.confidence}
          </p>
        </div>
        <div className="text-right">
          <span
            className={clsx("text-sm px-3 py-1 rounded-full font-bold", ratingClass(result.overall_rating))}
          >
            {result.overall_rating}
          </span>
          <p className="text-3xl font-bold mt-1" style={{ color: ratingColor(result.overall_score) }}>
            {result.overall_score.toFixed(0)}
          </p>
          <p className="text-xs text-slate-400">/ 100</p>
        </div>
      </div>

      {/* Overall bar */}
      <ScoreBar score={result.overall_score} />

      {/* Top hazards */}
      {result.top_hazards.length > 0 && (
        <p className="text-xs text-slate-300">
          Top hazards: <span className="text-orange-400 font-medium">{result.top_hazards.join(", ")}</span>
        </p>
      )}

      {/* Hazard breakdown */}
      <div className="mt-2">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Hazard Breakdown</p>
        {result.hazard_results.map((h) => (
          <HazardRow key={h.hazard} h={h} />
        ))}
      </div>

      {/* Data gaps */}
      {result.data_gaps.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-2 mt-2">
          <p className="text-xs font-semibold text-amber-400 mb-1">Data Gaps</p>
          {result.data_gaps.slice(0, 4).map((g, i) => (
            <p key={i} className="text-xs text-amber-300/80">{g}</p>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-slate-500 italic mt-2">{result.methodology_note}</p>
    </div>
  );
}
