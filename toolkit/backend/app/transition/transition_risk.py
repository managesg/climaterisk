"""
Transition risk engine. All outputs labelled as AI-generated interpretation
based on scenario frameworks (NGFS, IEA NZE). No financial values fabricated.
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# NGFS/IEA scenario descriptors
SCENARIO_POLICY_INTENSITY = {
    "SSP1-2.6": "high",
    "SSP2-4.5": "medium",
    "SSP5-8.5": "low",
    "NGFS_NET_ZERO": "very_high",
    "NGFS_DELAYED_TRANSITION": "high_abrupt",
    "NGFS_HOTHOUSE": "low",
}

HIGH_EXPOSURE_SECTORS = {
    "Energy", "Utilities", "Materials", "Industrials",
    "Real Estate", "Transportation", "Agriculture", "Mining"
}

CARBON_INTENSIVE_INDUSTRIES = {
    "Oil & Gas", "Coal Mining", "Steel", "Cement",
    "Aviation", "Shipping", "Thermal Power Generation",
    "Commercial Real Estate", "Industrial Real Estate"
}


class TransitionRiskEngine:
    def assess(
        self,
        sector: str,
        industry: str,
        geography: str,
        scenario: str,
        physical_risk_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        risks = []
        policy_intensity = SCENARIO_POLICY_INTENSITY.get(scenario, "medium")
        high_sector = sector in HIGH_EXPOSURE_SECTORS
        carbon_intensive = industry in CARBON_INTENSIVE_INDUSTRIES

        # --- Policy and legal ---
        risks.append(self._policy_risk(sector, industry, scenario, policy_intensity, geography))

        # --- Market risk ---
        risks.append(self._market_risk(sector, industry, scenario, carbon_intensive))

        # --- Technology risk ---
        risks.append(self._technology_risk(sector, industry, scenario))

        # --- Reputation risk ---
        risks.append(self._reputation_risk(sector, industry, scenario))

        # --- Insurance risk ---
        risks.append(self._insurance_risk(physical_risk_results, scenario))

        # --- Utilities / energy risk ---
        risks.append(self._utilities_risk(sector, industry, scenario))

        # --- Capital access ---
        risks.append(self._capital_access_risk(sector, industry, scenario))

        return risks

    def _policy_risk(self, sector, industry, scenario, policy_intensity, geography) -> Dict:
        severity = "High" if policy_intensity in ("high", "very_high", "high_abrupt") else "Moderate"
        scenario_note = {
            "NGFS_NET_ZERO": "Under NGFS Net Zero 2050, carbon prices reach >$250/tCO2e by 2050.",
            "NGFS_DELAYED_TRANSITION": "Delayed transition means abrupt policy tightening post-2030.",
            "SSP1-2.6": "Strong near-term carbon pricing and regulation expected.",
            "SSP2-4.5": "Moderate carbon pricing; sector-specific regulations increasing.",
            "SSP5-8.5": "Minimal near-term carbon policy; physical risks dominate.",
            "NGFS_HOTHOUSE": "No material policy tightening; high physical risk path.",
        }.get(scenario, "Scenario assumptions not available.")

        return {
            "category": "Policy and Legal",
            "risk_driver": "Carbon pricing, mandatory disclosure, and building efficiency standards",
            "description": (
                f"As a {sector} company operating in {geography}, regulatory requirements "
                f"for carbon reporting (SEC Climate Rule, ISSB IFRS S2, EU CSRD) are increasing. "
                f"Carbon pricing mechanisms may impose costs on {industry} operations. {scenario_note}"
            ),
            "severity": severity,
            "time_horizon": "2030" if policy_intensity in ("very_high", "high_abrupt") else "2040",
            "confidence": "medium",
            "scenario": scenario,
            "financial_impact_note": (
                "Financial impact requires carbon price assumptions, emissions inventory, "
                "and regulatory scope analysis. Not estimated without that data."
            ),
            "required_data": [
                "Scope 1 & 2 emissions (tCO2e)",
                "Carbon price pathway assumption",
                "Regulatory jurisdiction mapping",
                "Disclosed climate targets",
            ],
            "tcfd_disclosure_area": "Strategy — scenario analysis",
            "evidence": [
                "NGFS Climate Scenarios 2023: https://www.ngfs.net/ngfs-scenarios-portal/",
                "ISSB IFRS S2 Climate Disclosures: https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/",
            ],
            "data_source_type": "ai_generated",
        }

    def _market_risk(self, sector, industry, scenario, carbon_intensive) -> Dict:
        severity = "High" if carbon_intensive else "Moderate"
        return {
            "category": "Market",
            "risk_driver": "Demand shift away from carbon-intensive products and services",
            "description": (
                f"Market preferences are shifting toward lower-carbon alternatives. "
                f"{'Carbon-intensive operations in ' + industry + ' face revenue pressure.' if carbon_intensive else 'Market risk is moderate for ' + sector + '.'} "
                f"Under scenario {scenario}, transition acceleration may reshape demand by 2035–2045."
            ),
            "severity": severity,
            "time_horizon": "2040",
            "confidence": "low",
            "scenario": scenario,
            "financial_impact_note": "Revenue impact requires product mix analysis and demand curve modelling.",
            "required_data": ["Product/service revenue breakdown", "Customer carbon commitments", "Sector demand projections"],
            "tcfd_disclosure_area": "Strategy — risks and opportunities",
            "evidence": [
                "IEA World Energy Outlook 2023: https://www.iea.org/reports/world-energy-model",
                "NGFS Scenarios: https://www.ngfs.net/",
            ],
            "data_source_type": "ai_generated",
        }

    def _technology_risk(self, sector, industry, scenario) -> Dict:
        high_tech_exposure = industry in (
            "Thermal Power Generation", "Oil & Gas", "Steel", "Cement",
            "Commercial Real Estate", "Industrial Real Estate"
        )
        return {
            "category": "Technology",
            "risk_driver": "Costs of transitioning to low-carbon technologies and stranded asset risk",
            "description": (
                f"{'High exposure to technology transition costs in ' + industry + '.' if high_tech_exposure else 'Technology transition risk is moderate for ' + sector + '.'} "
                f"Building retrofits (heat pumps, electrification, energy efficiency) "
                f"represent material capital expenditure under {scenario}. "
                f"Assets built before 2000 face highest retrofit cost exposure."
            ),
            "severity": "High" if high_tech_exposure else "Moderate",
            "time_horizon": "2040",
            "confidence": "medium",
            "scenario": scenario,
            "financial_impact_note": "Retrofit cost estimates require per-asset energy audit data.",
            "required_data": ["Building energy audit", "Current HVAC/mechanical plant age", "Utility contracts"],
            "tcfd_disclosure_area": "Risk Management — technology transition",
            "evidence": [
                "IEA Net Zero by 2050: https://www.iea.org/reports/world-energy-model/net-zero-emissions-by-2050-scenario-nze",
            ],
            "data_source_type": "ai_generated",
        }

    def _reputation_risk(self, sector, industry, scenario) -> Dict:
        return {
            "category": "Reputation",
            "risk_driver": "Stakeholder, investor, and tenant expectations on climate action",
            "description": (
                f"Increasing ESG scrutiny from investors, tenants, lenders, and regulators "
                f"creates reputational risk for {sector} companies that do not demonstrate "
                f"credible climate strategy. Greenwashing risk is also elevated where "
                f"disclosure claims are not supported by underlying data."
            ),
            "severity": "Moderate",
            "time_horizon": "2030",
            "confidence": "medium",
            "scenario": scenario,
            "financial_impact_note": "Reputational impact is not quantifiable without investor sentiment data.",
            "required_data": ["Sustainability disclosure maturity", "Investor engagement record", "Tenant sustainability requirements"],
            "tcfd_disclosure_area": "Governance — oversight",
            "evidence": [
                "ISSB IFRS S2: https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/",
            ],
            "data_source_type": "ai_generated",
        }

    def _insurance_risk(self, physical_results: List[Dict], scenario: str) -> Dict:
        high_risk_props = [r for r in physical_results if r.get("overall_score", 0) > 60]
        has_high_risk = len(high_risk_props) > 0
        return {
            "category": "Insurance",
            "risk_driver": "Insurance premium increases and coverage withdrawal for high-risk assets",
            "description": (
                f"{'High physical risk scores indicate elevated insurance exposure.' if has_high_risk else 'Physical risk screening did not flag acute insurance concerns.'} "
                f"Insurers are withdrawing coverage from wildfire, flood, and coastal flood zones. "
                f"Premium increases of 20–100%+ have been reported in high-risk US markets (Florida, California). "
                f"Assets with replacement values above $10M in high-risk zones require specialist review."
            ),
            "severity": "High" if has_high_risk else "Moderate",
            "time_horizon": "2030",
            "confidence": "medium",
            "scenario": scenario,
            "financial_impact_note": "Insurance cost impact requires current policy terms and replacement values.",
            "required_data": ["Current insurance policies", "Asset replacement values", "Claims history"],
            "tcfd_disclosure_area": "Risk Management — insurance",
            "evidence": ["Physical risk screening results from this assessment"],
            "data_source_type": "ai_generated",
        }

    def _utilities_risk(self, sector, industry, scenario) -> Dict:
        utility_dependent = industry in (
            "Data Center", "Manufacturing", "Industrial Real Estate",
            "Healthcare", "Hospitality"
        )
        return {
            "category": "Utilities / Energy / Water",
            "risk_driver": "Energy cost volatility, grid decarbonisation requirements, and water scarcity",
            "description": (
                f"{'High utility dependency in ' + industry + ' creates material exposure.' if utility_dependent else 'Standard utility exposure for ' + sector + '.'} "
                f"Grid electricity is decarbonising: Scope 2 emissions will decrease as grid cleans up, "
                f"but energy costs may increase during transition. Water availability risk applies "
                f"to water-intensive operations in stressed basins."
            ),
            "severity": "High" if utility_dependent else "Low",
            "time_horizon": "2040",
            "confidence": "low",
            "scenario": scenario,
            "financial_impact_note": "Energy cost impact requires kWh consumption and tariff structure data.",
            "required_data": ["Annual energy consumption (MWh)", "Water consumption (m3)", "Utility contracts and tariff exposure"],
            "tcfd_disclosure_area": "Metrics and Targets — energy",
            "evidence": [
                "IEA World Energy Outlook: https://www.iea.org/reports/world-energy-model",
            ],
            "data_source_type": "ai_generated",
        }

    def _capital_access_risk(self, sector, industry, scenario) -> Dict:
        return {
            "category": "Capital Access / Financing",
            "risk_driver": "Green lending criteria, sustainability-linked financing, and stranded asset risk",
            "description": (
                f"Lenders and capital markets are embedding climate risk criteria. "
                f"Assets without climate disclosure may face higher borrowing costs or refinancing risk. "
                f"In the EU, taxonomy alignment is increasingly required for green bonds. "
                f"Under scenario {scenario}, capital cost divergence between green and brown assets widens."
            ),
            "severity": "Moderate",
            "time_horizon": "2040",
            "confidence": "low",
            "scenario": scenario,
            "financial_impact_note": "Cost of capital impact requires debt structure and lender covenant analysis.",
            "required_data": ["Debt/equity structure", "Lender ESG requirements", "Asset taxonomy alignment status"],
            "tcfd_disclosure_area": "Strategy — financial planning",
            "evidence": [
                "NGFS Scenarios Portal: https://www.ngfs.net/ngfs-scenarios-portal/",
            ],
            "data_source_type": "ai_generated",
        }
