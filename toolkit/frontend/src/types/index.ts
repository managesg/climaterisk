export type RiskRating = "Very Low" | "Low" | "Moderate" | "High" | "Very High";
export type TimeHorizon = "current" | "2030" | "2040" | "2050";
export type ClimateScenario = "SSP1-2.6" | "SSP2-4.5" | "SSP5-8.5" | "NGFS_NET_ZERO" | "NGFS_DELAYED_TRANSITION" | "NGFS_HOTHOUSE";
export type DataSourceType = "observed" | "modeled" | "scenario_assumption" | "ai_generated" | "user_provided" | "missing";

export interface Company {
  company_id: string;
  name: string;
  sector: string;
  industry: string;
  geography: string;
  revenue_usd?: number;
  emissions?: {
    scope_1_tco2e?: number;
    scope_2_tco2e?: number;
    scope_3_tco2e?: number;
    base_year?: number;
  };
  created_at: string;
}

export interface Property {
  property_id: string;
  company_id: string;
  name: string;
  latitude: number;
  longitude: number;
  country?: string;
  city?: string;
  asset_type: string;
  floor_area_m2?: number;
  year_built?: number;
  elevation_m?: number;
  distance_to_coast_km?: number;
  distance_to_river_km?: number;
  replacement_value_usd?: number;
  fema_flood_zone?: string;
}

export interface FeatureScore {
  feature_name: string;
  raw_value?: number;
  raw_unit?: string;
  normalized_score: number;
  data_source_type: DataSourceType;
  source_name?: string;
  source_url?: string;
  notes?: string;
}

export interface HazardResult {
  hazard: string;
  applicable: boolean;
  category_score: number;
  rating: RiskRating;
  feature_scores: FeatureScore[];
  top_drivers: string[];
  confidence: string;
  evidence: string[];
  data_gaps: string[];
  recommended_action: string;
  scenario: string;
  time_horizon: string;
}

export interface PhysicalRiskResult {
  property_id: string;
  property_name: string;
  overall_score: number;
  overall_rating: RiskRating;
  hazard_results: HazardResult[];
  top_hazards: string[];
  confidence: string;
  data_gaps: string[];
  scenario: string;
  time_horizon: string;
  methodology_note: string;
}

export interface TransitionRisk {
  category: string;
  risk_driver: string;
  description: string;
  severity: RiskRating;
  time_horizon: string;
  confidence: string;
  scenario: string;
  financial_impact_note: string;
  required_data: string[];
  tcfd_disclosure_area: string;
  evidence: string[];
  data_source_type: DataSourceType;
}

export interface Opportunity {
  title: string;
  category: string;
  description: string;
  linked_risks: string[];
  implementation_actions: string[];
  expected_benefit_type: string;
  financial_estimate_note: string;
  confidence: string;
  time_horizon: string;
  disclosure_relevance: string;
  data_source_type: DataSourceType;
}

export interface AgentRun {
  run_id: string;
  company_id: string;
  state: "pending" | "running" | "awaiting_human_review" | "completed" | "failed";
  workflow_steps_completed: string[];
  final_output?: Record<string, unknown>;
  confidence?: number;
  flags?: string[];
  error?: string;
  created_at: string;
  updated_at: string;
}

export type RiskScenario = {
  scenario: ClimateScenario;
  time_horizon: TimeHorizon;
};
