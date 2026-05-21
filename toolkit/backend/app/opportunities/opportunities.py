"""Climate opportunities identification engine."""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


ENERGY_INTENSIVE_SECTORS = {"Real Estate", "Industrials", "Utilities", "Materials"}
SERVICE_SECTORS = {"Financials", "Technology", "Health Care", "Communication Services"}


class OpportunitiesEngine:
    def identify(
        self,
        sector: str,
        industry: str,
        scenario: str,
        physical_risk_results: List[Dict[str, Any]],
        transition_risks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        opps = []
        opps.append(self._energy_efficiency(sector, industry, scenario))
        opps.append(self._renewable_energy(sector, industry, scenario))
        opps.append(self._resilience_adaptation(physical_risk_results, scenario))
        opps.append(self._green_products_services(sector, industry, scenario))
        opps.append(self._green_financing(sector, scenario))
        return opps

    def _energy_efficiency(self, sector, industry, scenario) -> Dict:
        return {
            "title": "Building Energy Efficiency Retrofit",
            "category": "Resource Efficiency",
            "description": (
                f"Energy efficiency improvements (LED lighting, HVAC upgrades, building envelope, "
                f"smart controls) can reduce energy costs 20–40% and improve asset value. "
                f"For {industry} assets, this also reduces Scope 1 and 2 emissions exposure."
            ),
            "linked_risks": ["Technology", "Utilities / Energy / Water", "Policy and Legal"],
            "required_data": ["Energy audit per building", "Baseline energy consumption (kWh)", "Current HVAC age"],
            "implementation_actions": [
                "Commission ASHRAE Level 2 energy audit for high-consumption assets",
                "Prioritise pre-2000 buildings for retrofit",
                "Set EUI (Energy Use Intensity) reduction target",
            ],
            "expected_benefit_type": "Cost reduction, emissions reduction, asset value uplift",
            "financial_estimate_note": "Financial benefit requires baseline energy cost and audit data.",
            "evidence": [
                "IEA Net Zero Scenario — buildings efficiency pathway",
                "ENERGY STAR Portfolio Manager benchmarking",
            ],
            "confidence": "medium",
            "time_horizon": "2030",
            "disclosure_relevance": "ISSB S2: Metrics and Targets — energy intensity; SASB Real Estate energy metrics",
            "data_source_type": "ai_generated",
        }

    def _renewable_energy(self, sector, industry, scenario) -> Dict:
        return {
            "title": "On-Site Renewable Energy and Storage",
            "category": "Energy Source",
            "description": (
                f"Rooftop solar PV and battery storage can reduce Scope 2 emissions and "
                f"provide energy cost certainty. Power Purchase Agreements (PPAs) offer "
                f"off-site renewable options without capital outlay. "
                f"Applicable to {industry} assets with adequate roof area and grid connection."
            ),
            "linked_risks": ["Utilities / Energy / Water", "Policy and Legal"],
            "required_data": ["Roof area (m2)", "Annual electricity consumption (kWh)", "Grid tariff structure"],
            "implementation_actions": [
                "Screen portfolio for solar suitability (roof area, orientation, shading)",
                "Model PPA vs capex solar economics",
                "Include renewable procurement in energy strategy",
            ],
            "expected_benefit_type": "Cost reduction, Scope 2 emissions reduction, energy resilience",
            "financial_estimate_note": "Savings require site-level solar yield and tariff data.",
            "evidence": [
                "IEA Solar PV global outlook",
                "NREL PVWatts calculator: https://pvwatts.nrel.gov/",
            ],
            "confidence": "medium",
            "time_horizon": "2030",
            "disclosure_relevance": "ISSB S2: Strategy — transition plan; SASB energy metrics",
            "data_source_type": "ai_generated",
        }

    def _resilience_adaptation(self, physical_results: List[Dict], scenario: str) -> Dict:
        high_risk = [r for r in physical_results if r.get("overall_score", 0) > 60]
        top_hazards = []
        for r in high_risk:
            top_hazards.extend(r.get("top_hazards", []))
        top_hazards = list(set(top_hazards))[:3]

        return {
            "title": "Physical Resilience Investment and Climate Adaptation",
            "category": "Resilience / Adaptation",
            "description": (
                f"Proactive adaptation investment in physical resilience "
                f"{'addressing: ' + ', '.join(top_hazards) if top_hazards else 'across the portfolio'} "
                f"can reduce insurance costs, protect asset value, and maintain business continuity. "
                f"Adaptation measures may qualify for green financing at preferential rates."
            ),
            "linked_risks": ["Insurance", "Capital Access / Financing"],
            "required_data": ["Replacement values", "Business interruption values", "Current flood/fire protection measures"],
            "implementation_actions": [
                "Prioritise high-risk assets for site-level resilience assessment",
                "Develop adaptation roadmap aligned with scenario time horizons",
                "Engage insurers on risk reduction credits",
            ],
            "expected_benefit_type": "Insurance cost reduction, avoided business interruption, asset value protection",
            "financial_estimate_note": "Benefit quantification requires replacement values and insurance premium data.",
            "evidence": ["Physical risk screening results from this assessment"],
            "confidence": "low",
            "time_horizon": "2040",
            "disclosure_relevance": "ISSB S2: Strategy — resilience; TCFD adaptation actions",
            "data_source_type": "ai_generated",
        }

    def _green_products_services(self, sector, industry, scenario) -> Dict:
        return {
            "title": "Green and Net-Zero Certified Assets",
            "category": "Products and Services",
            "description": (
                f"Green building certifications (LEED, BREEAM, NABERS, ENERGY STAR) "
                f"command rental premiums of 3–11% and lower vacancy rates in many markets. "
                f"Net-zero buildings are increasingly required by corporate occupiers with SBTi targets. "
                f"Relevant for {industry} assets in major commercial markets."
            ),
            "linked_risks": ["Reputation", "Market"],
            "required_data": ["Current building certifications", "Tenant sustainability requirements", "Market rental comparables"],
            "implementation_actions": [
                "Assess certification gap for top assets by value",
                "Develop green lease framework for new tenancies",
                "Track tenant Scope 3 building emission commitments",
            ],
            "expected_benefit_type": "Revenue uplift, tenant retention, market differentiation",
            "financial_estimate_note": "Green premium requires local market comparable analysis.",
            "evidence": [
                "CBRE/JLL green building premium studies",
                "USGBC LEED: https://www.usgbc.org/leed",
            ],
            "confidence": "low",
            "time_horizon": "2035",
            "disclosure_relevance": "ISSB S2: Strategy — opportunities; SASB Real Estate certification metrics",
            "data_source_type": "ai_generated",
        }

    def _green_financing(self, sector, scenario) -> Dict:
        return {
            "title": "Green Bonds, Sustainability-Linked Loans, and Green Financing",
            "category": "Markets",
            "description": (
                f"Climate-aligned assets and credible transition plans support access to "
                f"green bonds and sustainability-linked loans (SLLs) at preferential rates. "
                f"Under {scenario}, capital cost advantage of green assets widens. "
                f"EU Taxonomy alignment unlocks additional European capital pools."
            ),
            "linked_risks": ["Capital Access / Financing", "Reputation"],
            "required_data": ["Current debt structure", "Asset taxonomy alignment", "Sustainability KPIs for SLL covenants"],
            "implementation_actions": [
                "Map portfolio to EU Taxonomy technical screening criteria",
                "Identify assets eligible for green bond allocation",
                "Engage sustainability-linked loan structuring with lenders",
            ],
            "expected_benefit_type": "Reduced cost of capital, expanded investor universe, improved credit terms",
            "financial_estimate_note": "Financing benefit requires deal-specific term negotiation.",
            "evidence": [
                "ICMA Green Bond Principles: https://www.icmagroup.org/",
                "EU Taxonomy Regulation",
            ],
            "confidence": "low",
            "time_horizon": "2035",
            "disclosure_relevance": "ISSB S2: Strategy — financial planning; TCFD strategy resilience",
            "data_source_type": "ai_generated",
        }
