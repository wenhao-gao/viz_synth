"""Render a synthesis tree as a directed graph with molecule images."""

from __future__ import annotations

import io
import tempfile

import PIL.Image
import pydot
from rdkit import Chem
from rdkit.Chem import Draw

from .models import BuildingBlock, ReactionNode


def draw_molecule(smiles: str, size: int = 200) -> PIL.Image.Image | None:
    """Render a SMILES string as a transparent-background PNG image."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    d2d = Draw.MolDraw2DCairo(size, size)
    opts = d2d.drawOptions()
    opts.setBackgroundColour((1, 1, 1, 0))
    opts.setAtomPalette({0: (0.0, 0.0, 0.0)})
    opts.minFontSize = 20
    d2d.DrawMolecule(mol)
    d2d.FinishDrawing()
    img_data = d2d.GetDrawingText()
    return PIL.Image.open(io.BytesIO(img_data))


def _make_node(
    tmpdir: str,
    node_name: str,
    image: PIL.Image.Image | None,
    annots: dict[str, str | None],
    fontname: str,
) -> pydot.Node:
    """Create a pydot node with an HTML label containing an image and annotations."""
    label_lines = [
        "<",
        '<TABLE STYLE="ROUNDED" BORDER="0" CELLBORDER="0" CELLSPACING="5" CELLPADDING="0" BGCOLOR="grey97">',
    ]
    if image is not None:
        im_path = f"{tmpdir}/{node_name}.png"
        image.save(im_path)
        label_lines.append(f'<TR><TD><IMG SRC="{im_path}"/></TD></TR>')

    for k, v in annots.items():
        if v is not None and v != "":
            if k:
                label_lines.append(f"<TR><TD>{k}: {v}</TD></TR>")
            else:
                label_lines.append(f"<TR><TD>{v}</TD></TR>")

    label_lines += ["</TABLE>", ">"]

    return pydot.Node(
        node_name,
        shape="plaintext",
        label="".join(label_lines),
        fontsize="11",
        fontname=fontname,
    )


def draw_synthesis_tree(
    nodes: list[BuildingBlock | ReactionNode],
    node_image_size: int = 200,
    rankdir: str = "LR",
    fontname: str = "Fira Sans",
    dpi: int = 200,
) -> PIL.Image.Image:
    """Render a list of synthesis tree roots as a directed graph PNG."""
    counter = [0]

    with tempfile.TemporaryDirectory() as tmpdir:
        graph = pydot.Dot(
            "",
            graph_type="digraph",
            rankdir=rankdir,
            fontname=fontname,
            fontsize=8,
            dpi=dpi,
            bgcolor="transparent",
            nodesep=0.02,
        )

        for root in nodes:
            _add_node(graph, root, tmpdir, node_image_size, fontname, counter)

        png_data = graph.create_png()
        return PIL.Image.open(io.BytesIO(png_data))


def _add_node(
    graph: pydot.Dot,
    node: BuildingBlock | ReactionNode,
    tmpdir: str,
    node_image_size: int,
    fontname: str,
    counter: list[int],
) -> str:
    """Recursively add a node and its children to the graph. Returns the node's ID."""
    counter[0] += 1
    node_id = f"n{counter[0]}"

    if isinstance(node, BuildingBlock):
        img = draw_molecule(node.smiles, size=node_image_size)
        annots: dict[str, str | None] = {
            "": node.bb_index,
        }
        if node.id:
            annots["ID"] = node.id
        graph.add_node(_make_node(tmpdir, node_id, img, annots, fontname))

    elif isinstance(node, ReactionNode):
        # Draw first product molecule if available
        prod_img = None
        if node.products:
            prod_img = draw_molecule(node.products[0], size=node_image_size)

        annots = {
            "Reaction": node.rxn_index,
        }
        graph.add_node(_make_node(tmpdir, node_id, prod_img, annots, fontname))

        # Recursively add reactants and connect edges
        for reactant in node.reactants:
            child_id = _add_node(graph, reactant, tmpdir, node_image_size, fontname, counter)
            graph.add_edge(pydot.Edge(child_id, node_id, color="grey50"))

    return node_id
