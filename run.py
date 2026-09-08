"""
PRAGATI AI — Startup Runner
Launches the FastAPI backend and serves the enterprise planner UI on http://127.0.0.1:8000
"""

import os
import sys
import types

# Zero-dependency Click shim for uvicorn programmatic execution
if "click" not in sys.modules:
    try:
        import click
    except ImportError:
        dummy_click = types.ModuleType("click")
        dummy_click.echo = print
        dummy_click.style = lambda text, **kw: text
        dummy_click.secho = lambda text, **kw: print(text)
        dummy_click.Choice = lambda *a, **k: None
        dummy_click.Path = lambda *a, **k: None
        dummy_click.command = lambda *a, **k: (lambda f: f)
        dummy_click.option = lambda *a, **k: (lambda f: f)
        dummy_click.argument = lambda *a, **k: (lambda f: f)
        dummy_click.group = lambda *a, **k: (lambda f: f)
        dummy_click.INT = int
        dummy_click.STRING = str
        dummy_click.BOOL = bool
        sys.modules["click"] = dummy_click

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print("=" * 70)
    print("  PRAGATI AI — Planning-to-Execution Intelligence Layer")
    print("  SIH26122 - Oil India Limited | Team: InfraNexus")
    print("=" * 70)
    print(f"  Local Access:       http://127.0.0.1:{port}")
    print(f"  LAN / Mobile / IP:  http://0.0.0.0:{port}")
    print(f"  API Documentation:  http://127.0.0.1:{port}/docs")
    print(f"  Health Endpoint:    http://127.0.0.1:{port}/health")
    print("=" * 70)
    
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
