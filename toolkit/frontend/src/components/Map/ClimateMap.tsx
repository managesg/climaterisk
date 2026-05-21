"use client";
import { useMemo } from "react";
import type { Property, PhysicalRiskResult } from "@/types";

function ratingColor(score: number): [number, number, number] {
  if (score <= 20) return [22, 163, 74];
  if (score <= 40) return [101, 163, 13];
  if (score <= 60) return [202, 138, 4];
  if (score <= 80) return [234, 88, 12];
  return [220, 38, 38];
}

interface Props {
  properties: Property[];
  riskResults: PhysicalRiskResult[];
  selectedId?: string;
  onSelectProperty: (id: string) => void;
}

export default function ClimateMap({ properties, riskResults, selectedId, onSelectProperty }: Props) {
  const riskMap = useMemo(
    () => Object.fromEntries(riskResults.map((r) => [r.property_id, r])),
    [riskResults]
  );

  if (properties.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-900 rounded-xl border border-slate-700">
        <div className="text-center text-slate-500">
          <p className="text-4xl mb-3">🗺️</p>
          <p className="text-sm">Add properties to view them on the map</p>
          <p className="text-xs mt-1 text-slate-600">Map uses Mapbox GL / MapLibre — token required for satellite tiles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-slate-900 rounded-xl border border-slate-700 relative overflow-hidden">
      <div className="absolute inset-0 p-4">
        <div className="grid grid-cols-1 gap-2 overflow-auto h-full">
          {properties.map((p) => {
            const risk = riskMap[p.property_id];
            const score = risk?.overall_score ?? 0;
            const [r, g, b] = ratingColor(score);
            const isSelected = p.property_id === selectedId;
            return (
              <div
                key={p.property_id}
                onClick={() => onSelectProperty(p.property_id)}
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                  isSelected ? "bg-slate-600" : "bg-slate-800 hover:bg-slate-700"
                }`}
              >
                <div
                  className="w-4 h-4 rounded-full flex-shrink-0 border-2 border-white/30"
                  style={{ background: `rgb(${r},${g},${b})` }}
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{p.name}</p>
                  <p className="text-xs text-slate-400">
                    {p.latitude.toFixed(4)}, {p.longitude.toFixed(4)}
                  </p>
                </div>
                {risk && (
                  <div className="ml-auto text-right flex-shrink-0">
                    <p className="font-bold text-sm" style={{ color: `rgb(${r},${g},${b})` }}>
                      {score.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-400">{risk.overall_rating}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <div className="absolute bottom-3 right-3 text-xs text-slate-600">
        Map: Mapbox GL recommended (token via NEXT_PUBLIC_MAPBOX_TOKEN)
      </div>
    </div>
  );
}
