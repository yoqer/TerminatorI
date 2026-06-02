"""CLI mínima para TERMINATORI."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer

from terminatori import TerminatorI, TerminatorIConfig
from terminatori.api.app import main as server_main

app = typer.Typer(help="CLI de TERMINATORI")


@app.command()
def serve() -> None:
    """Inicia el servidor FastAPI."""
    server_main()


@app.command()
def infer(
    prompt: str,
    model: Optional[str] = typer.Option(None, help="Modelo a usar, por ejemplo openai/gpt-4o-mini"),
) -> None:
    """Ejecuta una inferencia simple desde terminal."""

    async def _run() -> None:
        cfg = TerminatorIConfig()
        if model:
            cfg.model = model
        engine = TerminatorI(cfg)
        await engine.start()
        try:
            result = await engine.infer(prompt)
            typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        finally:
            await engine.stop()

    asyncio.run(_run())


if __name__ == "__main__":
    app()
