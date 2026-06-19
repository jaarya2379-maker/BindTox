from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BindingSummary:
    strongest_binding: bool
    affinity_band: str
    interpretation: str
    likely_interactions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strongest_binding": self.strongest_binding,
            "affinity_band": self.affinity_band,
            "interpretation": self.interpretation,
            "likely_interactions": self.likely_interactions,
        }


def summarize_binding(binding_energy: float | None, descriptors: dict[str, Any]) -> BindingSummary | None:
    if binding_energy is None:
        return None

    if binding_energy <= -9:
        affinity_band = "High affinity"
        interpretation = "Strong binding predicted before wet-lab validation."
    elif binding_energy <= -7:
        affinity_band = "Moderate affinity"
        interpretation = "Promising binding signal that may justify deeper screening."
    else:
        affinity_band = "Weak affinity"
        interpretation = "Binding is detectable but not especially strong in this simulation."

    likely_interactions: list[str] = []
    if descriptors.get("h_bond_donors", 0) or descriptors.get("h_bond_acceptors", 0):
        likely_interactions.append("Hydrogen-bonding potential present")
    if descriptors.get("logp", 0) >= 1:
        likely_interactions.append("Hydrophobic contacts likely contribute")
    if descriptors.get("tpsa", 0) > 75:
        likely_interactions.append("Polar surface may affect pocket fit")
    if not likely_interactions:
        likely_interactions.append("General shape complementarity may dominate")

    return BindingSummary(
        strongest_binding=binding_energy <= -7,
        affinity_band=affinity_band,
        interpretation=interpretation,
        likely_interactions=likely_interactions,
    )
