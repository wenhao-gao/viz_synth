"""Parse prexsyn's synthesis_to_string() output into a tree of dataclasses."""

from __future__ import annotations

import re

from .models import BuildingBlock, ReactionNode


def parse_synthesis(text: str) -> list[BuildingBlock | ReactionNode]:
    """Parse synthesis text into a list of root nodes.

    The text format is produced by prexsyn's ``synthesis_to_string()``.
    Top-level items are separated by being at the same base indentation level.
    """
    lines = text.splitlines()
    # Remove trailing empty lines
    while lines and lines[-1].strip() == "":
        lines.pop()
    if not lines:
        return []

    # Find the minimum indentation of lines starting with "- "
    base_indent = _find_base_indent(lines)

    # Split into top-level item blocks
    blocks = _split_into_blocks(lines, base_indent)

    return [_parse_block(block, base_indent) for block in blocks]


def _find_base_indent(lines: list[str]) -> int:
    """Find the indentation of the first line starting with '- '."""
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("- "):
            return len(line) - len(stripped)
    return 0


def _split_into_blocks(lines: list[str], base_indent: int) -> list[list[str]]:
    """Split lines into blocks, each starting with a '- ' at base_indent level."""
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # A new top-level item starts with "- " at exactly the base indent
        if indent == base_indent and stripped.startswith("- ") and current_block:
            blocks.append(current_block)
            current_block = []
        current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return blocks


def _parse_block(lines: list[str], base_indent: int) -> BuildingBlock | ReactionNode:
    """Parse a single block into a BuildingBlock or ReactionNode."""
    first_line = lines[0].strip()

    if first_line.startswith("- SMILES:"):
        return _parse_building_block(lines)
    elif first_line.startswith("- Reaction Index:"):
        return _parse_reaction_node(lines, base_indent)
    else:
        raise ValueError(f"Unexpected block start: {first_line!r}")


def _parse_building_block(lines: list[str]) -> BuildingBlock:
    """Parse a building block from its lines."""
    smiles = ""
    bb_index = ""
    bb_id = None

    for line in lines:
        stripped = line.strip()
        if m := re.match(r"- SMILES:\s*(.+)", stripped):
            smiles = m.group(1).strip()
        elif m := re.match(r"Building Block Index:\s*(.+)", stripped):
            bb_index = m.group(1).strip()
        elif m := re.match(r"ID:\s*(.+)", stripped):
            bb_id = m.group(1).strip()

    return BuildingBlock(smiles=smiles, bb_index=bb_index, id=bb_id)


def _parse_reaction_node(lines: list[str], base_indent: int) -> ReactionNode:
    """Parse a reaction node, including nested reactants."""
    first_line = lines[0].strip()
    m = re.match(r"- Reaction Index:\s*(.+)", first_line)
    if not m:
        raise ValueError(f"Expected Reaction Index line, got: {first_line!r}")
    rxn_index = m.group(1).strip()

    # Find sections: Possible Products and Reactants
    products: list[str] = []
    reactants: list[BuildingBlock | ReactionNode] = []

    section = None
    # Section headers like "  Possible Products:" sit at base_indent + 2
    header_indent = base_indent + 2
    reactant_lines: list[str] = []
    reactant_base_indent: int | None = None

    for line in lines[1:]:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        # Only detect section headers at the expected indentation for *this* node
        if indent == header_indent and stripped == "Possible Products:":
            section = "products"
            continue
        elif indent == header_indent and stripped == "Reactants:":
            section = "reactants"
            continue

        if section == "products":
            if m := re.match(r"- (.+)", stripped):
                products.append(m.group(1).strip())
        elif section == "reactants":
            # Collect all reactant lines and parse them as sub-blocks
            reactant_lines.append(line)
            if reactant_base_indent is None and stripped.startswith("- "):
                reactant_base_indent = indent

    # Parse the collected reactant lines into sub-blocks
    if reactant_lines and reactant_base_indent is not None:
        sub_blocks = _split_into_blocks(reactant_lines, reactant_base_indent)
        for block in sub_blocks:
            reactants.append(_parse_block(block, reactant_base_indent))

    return ReactionNode(rxn_index=rxn_index, products=products, reactants=reactants)
