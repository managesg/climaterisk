"use client";

import type { HazardScore, HazardType, RiskRating } from "../lib/types";

const HAZARD_LABELS: Record<HazardType, string> = {
  wildfire: "Wildfire",
  inland_flood: "Inland Flood",
  coastal_flood: "Coastal Flood / SLR",
  heat_stress: "Heat Stress",
  drought: "Drought / Water",
  wind_hurricane: "Wind / Hurricane",
};

const RATING_COLORS: Record<RiskRating, string> = {
  very_low: "bg-green-100 text-green-800",
  low: "bg-lime-100 text-lime-800",
  moderate: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  very_high: "bg-red-100 text-red-800",
};

const RATING_LABELS: Record<RiskRating, string> = {
  very_low: "Very Low",
  low: "Low",
  moderate: "Moderate",
  high: "High",
  very_high: "Very High",
};

interface Props {
  hazardScores: Partial<Record<HazardType, HazardScore>>;
  overallScore?: number;
  overallRating?: RiskRating;
}

export function RiskScorecard({ hazardScores, overallScore, overallRating }: Props) {
  return (
    <div className="space-y-4">
      {overallScore !== undefined && overallRating && (
        <div className="p-4 rounded-lg border-2 border-gray-300 bg-gray-50">
          <div className="flex justify-between items-center">
            <span className="font-bold text-lg">Overall Physical Risk</span>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold">{overallScore.toFixed(1)}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${RATING_COLORS[overallRating]}`}>
                {RATING_LABELS[overallRating]}
              </span>
            </div>
          </div>
          <ScoreBar score={overallScore} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {Object.entries(hazardScores).map(([hazard, score]) => (
          <HazardCard
            key={hazard}
            hazard={hazard as HazardType}
            score={score as HazardScore}
          />
        ))}
      </div>
    </div>
  );
}

function HazardCard({ hazard, score }: { hazard: HazardType; score: HazardScore }) {
  return (
    <div className="p-3 rounded-lg border border-gray-200 bg-white">
      <div className="flex justify-between items-start mb-2">
        <span className="font-medium text-sm">{HAZARD_LABELS[hazard]}</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${RATING_COLORS[score.rating]}`}>
          {RATING_LABELS[score.rating]}
        </span>
      </div>
      <ScoreBar score={score.category_score} />
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span>Score: {score.category_score.toFixed(1)}/100</span>
        <span>Confidence: {(score.confidence * 100).toFixed(0)}%</span>
      </div>
      {score.data_gaps.length > 0 && (
        <div className="mt-1 text-xs text-amber-600">
          ⚠ {score.data_gaps.length} data gap{score.data_gaps.length > 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score <= 20 ? "bg-green-500" :
    score <= 40 ? "bg-lime-500" :
    score <= 60 ? "bg-yellow-500" :
    score <= 80 ? "bg-orange-500" : "bg-red-500";

  return (
    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
      <div
        className={`h-2 rounded-full ${color}`}
        style={{ width: `${Math.min(100, score)}%` }}
      />
    </div>
  );
}
