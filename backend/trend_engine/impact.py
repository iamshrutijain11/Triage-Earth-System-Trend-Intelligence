"""
Climate Trend Impact Coupling Engine.

Bridges multi-decadal Earth observation trends with ground-level hazard probabilities
and physical infrastructure exposure.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import numpy as np

from trend_engine.models import TrendResult


@dataclass
class ImpactAssessment:
    """Scientific impact assessment coupling a climate trend to hazard risk."""
    variable_name: str
    region_name: str
    trend_slope: float
    slope_unit: str
    is_statistically_significant: bool
    extreme_event_frequency_shift_pct: float
    projected_exceedance_probability_change: str
    impact_vulnerability_index: float  # 0 to 100
    impact_category: str  # "Low", "Moderate", "High", "Critical"
    infrastructure_implications: List[str]
    tactical_recommendations: List[str]
    confidence_level: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_climate_trend_impact(
    trend_result: TrendResult,
    region_name: str,
    baseline_asset_summary: Optional[Dict[str, Any]] = None,
) -> ImpactAssessment:
    """Compute the operational impact of a detected Earth-system trend.

    Parameters
    ----------
    trend_result : TrendResult
        Statistical result from TrendAnalyzer.
    region_name : str
        Name of the geographic region under study.
    baseline_asset_summary : dict, optional
        Summary metrics from triage engine (damaged buildings, roads, bridges).

    Returns
    -------
    ImpactAssessment
    """
    slope = trend_result.sens_slope
    is_sig = trend_result.is_statistically_significant
    var_lower = trend_result.variable_name.lower()

    freq_shift = 0.0
    ivi_score = 15.0  # baseline

    implications: List[str] = []
    recommendations: List[str] = []

    if "precip" in var_lower:
        if is_sig and slope > 0:
            # Positive precipitation trend -> amplified flood / flash flood / debris flow risk
            freq_shift = min(85.0, abs(slope) * 6.5)
            ivi_score = 45.0 + freq_shift * 0.6
            implications = [
                f"Statistically significant upward rainfall trend ({slope:+.3f} {trend_result.slope_unit}) elevates peak runoff volume in mountain riverbeds.",
                "Shortens return periods of 50-year and 100-year flash floods, increasing hydraulic scour on bridges.",
                "Steep river corridor slopes face accelerated saturation, triggering compounding debris flows and road severance.",
            ]
            recommendations = [
                "Re-evaluate design discharge criteria for bridges along the highway corridor.",
                "Prioritize non-structural early warning telemetry in high-gradient mountain settlements.",
                "Maintain designated elevated Helicopter Landing Zones (HLZs) above 20-meter HAND drainage margins.",
            ]
        elif is_sig and slope < 0:
            freq_shift = min(60.0, abs(slope) * 4.5)
            ivi_score = 35.0 + freq_shift * 0.4
            implications = [
                "Statistically significant downward precipitation trend threatens agricultural water storage and dry-season baseflow.",
                "Increases agricultural drought vulnerability and lowers hydropower reservoir recharging rates.",
            ]
            recommendations = [
                "Implement community rainwater harvesting and off-channel storage reservoirs.",
                "Enforce irrigation efficiency measures during low-flow winter months.",
            ]
        else:
            implications = ["No statistically significant long-term trend detected in precipitation. Natural inter-annual monsoon variability dominates."]
            recommendations = ["Continue baseline hydrometric monitoring without immediate structural zoning revisions."]

    elif "temp" in var_lower:
        if is_sig and slope > 0:
            freq_shift = min(75.0, abs(slope) * 22.0)
            ivi_score = 40.0 + freq_shift * 0.7
            implications = [
                f"Rapid warming rate of {slope:+.3f} {trend_result.slope_unit} accelerates cryosphere degradation and glacial retreat.",
                "Accelerated glacial melt increases hydrostatic pressure in proglacial moraine dams, compounding GLOF risk.",
                "Higher temperatures amplify evapotranspiration, reducing shallow soil moisture between precipitation pulses.",
            ]
            recommendations = [
                "Integrate real-time satellite radar InSAR deformation monitoring on moraine-dammed high-altitude lakes.",
                "Adopt heat-resilient crop varieties in lower valley alluvial zones.",
            ]
        else:
            implications = ["Temperature trend remains within baseline decadal variability limits."]
            recommendations = ["Maintain regular automated weather station network coverage."]

    else:
        # Soil moisture, solar, NDVI, etc.
        freq_shift = min(40.0, abs(slope) * 15.0)
        ivi_score = 25.0 + freq_shift
        implications = [f"Gradual evolution observed in {trend_result.variable_name} ({slope:+.4f} {trend_result.slope_unit})."]
        recommendations = ["Monitor seasonal biomass changes and ground wetness variations."]

    # If baseline assets exist from triage run, enrich context and scale IVI
    if baseline_asset_summary:
        bldgs = baseline_asset_summary.get("total_damaged_buildings", 0)
        roads_km = baseline_asset_summary.get("total_damaged_roads_km", 0.0)
        if bldgs > 0 or roads_km > 0:
            asset_exposure_boost = min(20.0, bldgs * 0.2 + roads_km * 0.5)
            ivi_score += asset_exposure_boost
            implications.append(
                f"Coupled with tactical triage data: Ground observations reveal {bldgs} exposed buildings "
                f"and {roads_km:.1f} km of compromised road network vulnerable to recurrent trend-driven inundation."
            )

    ivi_score = min(100.0, max(0.0, ivi_score))

    if ivi_score >= 70.0:
        impact_category = "Critical"
    elif ivi_score >= 50.0:
        impact_category = "High"
    elif ivi_score >= 30.0:
        impact_category = "Moderate"
    else:
        impact_category = "Low"

    exceedance_text = (
        f"+{freq_shift:.1f}% estimated probability increase for 50-year extreme events"
        if freq_shift > 0 else "Baseline recurrence frequency unchanged"
    )

    confidence = "High (p < 0.01)" if trend_result.p_value < 0.01 else ("Moderate (p < 0.05)" if is_sig else "Low (Non-significant)")

    return ImpactAssessment(
        variable_name=trend_result.variable_name,
        region_name=region_name,
        trend_slope=round(float(slope), 6),
        slope_unit=trend_result.slope_unit,
        is_statistically_significant=is_sig,
        extreme_event_frequency_shift_pct=round(float(freq_shift), 1),
        projected_exceedance_probability_change=exceedance_text,
        impact_vulnerability_index=round(float(ivi_score), 1),
        impact_category=impact_category,
        infrastructure_implications=implications,
        tactical_recommendations=recommendations,
        confidence_level=confidence,
    )
