from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BuildingBlock:
    smiles: str
    bb_index: str
    id: str | None = None


@dataclass
class ReactionNode:
    rxn_index: str
    products: list[str] = field(default_factory=list)
    reactants: list[BuildingBlock | ReactionNode] = field(default_factory=list)
