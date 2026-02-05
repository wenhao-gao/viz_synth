"""FastAPI web server for synthesis pathway visualization."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .draw import draw_synthesis_tree
from .parser import parse_synthesis

app = FastAPI(title="Synthesis Path Visualization")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class VisualizeRequest(BaseModel):
    text: str
    rankdir: str = "LR"
    node_image_size: int = 200
    dpi: int = 200


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/visualize")
async def visualize(req: VisualizeRequest):
    nodes = parse_synthesis(req.text)
    if not nodes:
        return StreamingResponse(io.BytesIO(b""), media_type="text/plain", status_code=400)

    img = draw_synthesis_tree(
        nodes,
        node_image_size=req.node_image_size,
        rankdir=req.rankdir,
        dpi=req.dpi,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
