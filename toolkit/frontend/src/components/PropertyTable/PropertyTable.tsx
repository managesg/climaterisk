"use client";
import type { Property, PhysicalRiskResult } from "@/types";
import clsx from "clsx";

function ratingClass(score: number) {
  if (score <= 20) return "text-green-400";
  if (score <= 40) return "text-lime-400";
  if (score <= 60) return "text-yellow-400";
  if (score <= 80) return "text-orange-400";
  return "text-red-400";
}

interface Props {
  properties: Property[];
  riskResults: PhysicalRiskResult[];
  onSelect: (p: Property) => void;
  selectedId?: string;
}

export default function PropertyTable({ properties, riskResults, onSelect, selectedId }: Props) {
  const riskMap = Object.fromEntries(riskResults.map((r) => [r.property_id, r]));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
            <th className="text-left py-2 px-3">Property</th>
            <th className="text-left py-2 px-3">Type</th>
            <th className="text-left py-2 px-3">Location</th>
            <th className="text-right py-2 px-3">Risk Score</th>
            <th className="text-right py-2 px-3">Rating</th>
            <th className="text-left py-2 px-3">Top Hazard</th>
          </tr>
        </thead>
        <tbody>
          {properties.map((p) => {
            const risk = riskMap[p.property_id];
            const isSelected = p.property_id === selectedId;
            return (
              <tr
                key={p.property_id}
                onClick={() => onSelect(p)}
                className={clsx(
                  "border-b border-slate-700/50 cursor-pointer hover:bg-slate-700/40 transition-colors",
                  isSelected && "bg-brand-700/20"
                )}
              >
                <td className="py-2 px-3 font-medium text-slate-200">{p.name}</td>
                <td className="py-2 px-3 text-slate-400">{p.asset_type}</td>
                <td className="py-2 px-3 text-slate-400">
                  {[p.city, p.country].filter(Boolean).join(", ") || `${p.latitude.toFixed(2)}, ${p.longitude.toFixed(2)}`}
                </td>
                <td className={clsx("py-2 px-3 text-right font-bold", risk ? ratingClass(risk.overall_score) : "text-slate-500")}>
                  {risk ? risk.overall_score.toFixed(0) : "—"}
                </td>
                <td className="py-2 px-3 text-right text-slate-300">
                  {risk ? risk.overall_rating : "—"}
                </td>
                <td className="py-2 px-3 text-orange-400 text-xs">
                  {risk?.top_hazards?.[0] || "—"}
                </td>
              </tr>
            );
          })}
          {properties.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-slate-500">
                No properties yet. Add a property to begin screening.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
