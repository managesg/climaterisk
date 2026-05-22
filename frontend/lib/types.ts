// Types matching seabridge Pydantic models

export type DataType =
  | "observed"
  | "modeled"
  | "scenario"
  | "ai_generated"
  | "user_provided"
  | "missing";

export type RiskRating = "very_low" | "low" | "moderate" | "high" | "very_high";

export type HazardType =
  | "wildfire"
  | "inland_flood"
  | "coastal_flood"
  | "heat_stress"
  | "drought"
  | "wind_hurricane";

export type Scenario = "ssp126" | "ssp245" | "ssp585";

export interface Company {
  company_id: string;
  name: string;
  sector: string;
  industry: string;
  geography: string;
  revenue?: number;
  asset_value?: number;
  emissions?: number;
  energy_use?: number;
  water_use?: number;
  reporting_boundary?: string;
}

export interface Property {
  property_id: string;
  company_id: string;
  name: string;
  address?: string;
  latitude: number;
  longitude: number;
  country?: string;
  state?: string;
  city?: string;
  asset_type: string;
  floor_area?: number;
  year_built?: number;
  occupancy?: string;
  construction_type?: string;
  elevation?: number;
  distance_to_coast?: number;
  distance_to_river?: number;
  replacement_value?: number;
}

export interface FeatureScoreRecord {
  feature_name: string;
  raw_value?: number | string | null;
  normalized_score: number;
  source: string;
  source_url?: string;
  data_type: DataType;
  is_available: boolean;
  confidence: number;
  note?: string;
}

export interface HazardScore {
  hazard: HazardType;
  feature_scores: FeatureScoreRecord[];
  category_score: number;
  rating: RiskRating;
  confidence: number;
  top_drivers: string[];
  data_gaps: string[];
  recommended_action?: string;
}

export interface RiskAssessment {
  assessment_id: string;
  property_id: string;
  company_id: string;
  scenario: Scenario;
  time_horizon: number;
  hazard_scores: Record<HazardType, HazardScore>;
  overall_score?: number;
  overall_rating?: RiskRating;
  confidence: number;
  data_gaps: string[];
  assumptions: string[];
  created_at: string;
}

export interface AgentRunResult {
  run_id: string;
  status: "complete" | "pending_review" | "error";
  confidence?: number;
  data_gaps_count?: number;
  physical_risk_results?: Record<string, { overall_score: number; assessment_id: string }>;
  transition_risk?: Record<string, unknown>;
  opportunities?: Record<string, unknown>;
  nature_risk?: Record<string, unknown>;
  disclosure_draft?: string;
  errors?: string[];
}
