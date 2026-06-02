"""Gestor ligero de vídeo para despliegue estándar."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class VideoManager:
    def __init__(self, config=None):
        self.config = config
        self.output_dir = Path("./data/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runway_key = getattr(config, "runway_api_key", None) if config else None

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {"id": "runway", "name": "Runway", "configured": bool(self.runway_key)},
            {"id": "svd", "name": "Stable Video Diffusion", "configured": False},
            {"id": "fal", "name": "fal.ai", "configured": False},
            {"id": "minimax", "name": "MiniMax", "configured": False},
            {"id": "luma", "name": "Luma", "configured": False},
        ]

    async def generate(
        self,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        duration: int = 5,
        provider: str = "runway",
    ) -> Dict[str, Any]:
        available = [item["id"] for item in self.list_providers()]
        if provider not in available:
            return {"error": f"Unknown provider: {provider}", "available": available}
        if not prompt and not image_url:
            return {"error": "prompt or image_url is required"}
        target = self.output_dir / f"video_{provider}_{duration}s.txt"
        target.write_text(f"prompt={prompt}\nimage_url={image_url}\nduration={duration}\nprovider={provider}\n")
        return {
            "success": True,
            "provider": provider,
            "duration": duration,
            "output_path": str(target),
            "note": "Salida placeholder lista para integrar generación real.",
        }
