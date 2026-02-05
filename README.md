# viz_synth

A web app that visualizes chemistry synthesis pathways as directed graphs with molecule structure images. Accepts the text format produced by [prexsyn](https://github.com/luost26/prexsyn)'s `synthesis_to_string()`, parses it into a tree, and renders it using RDKit + pydot.

## File Structure

```
viz_synth/
├── app.py              # FastAPI app, routes, main entry point
├── models.py           # Dataclasses: BuildingBlock, ReactionNode
├── parser.py           # Parse synthesis text → tree of dataclasses
├── draw.py             # Render tree → PNG image (RDKit + pydot)
└── templates/
    └── index.html      # Single-page UI: textarea + image display
```

## Requirements

- Python >= 3.11
- System graphviz (`apt install graphviz` or `conda install conda-forge::graphviz`)
- Python packages listed in `requirements.txt`:
  - fastapi, uvicorn
  - rdkit, pydot, Pillow
  - jinja2, python-multipart

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn viz_synth.app:app --reload
```

Then open http://localhost:8000 in a browser. Paste synthesis text into the textarea and click **Visualize**
