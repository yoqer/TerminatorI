"""Gestor ligero de avatar para despliegue estándar."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class AvatarManager:
    def __init__(self, config=None):
        self.config = config
        self.models_dir = Path("./data/avatars")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.fal_api_key = getattr(config, "fal_api_key", None) if config else None

    async def generate(
        self,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        avatar_type: str = "3d",
        quality: str = "standard",
    ) -> Dict[str, Any]:
        if not prompt and not image_url:
            return {"error": "prompt or image_url is required"}
        file_name = f"avatar_{avatar_type}_{quality}.json"
        target = self.models_dir / file_name
        target.write_text(f'{{"prompt": {prompt!r}, "image_url": {image_url!r}, "type": {avatar_type!r}, "quality": {quality!r}}}')
        return {
            "success": True,
            "type": avatar_type,
            "quality": quality,
            "path": str(target),
            "note": "Generación local placeholder lista para integrarse con proveedor real.",
        }

    def list_local_models(self) -> List[Dict[str, Any]]:
        models = []
        for file in self.models_dir.glob("*"):
            models.append({"name": file.name, "path": str(file), "type": file.suffix.lstrip(".") or "data"})
        return models

    def import_model(self, source_path: str) -> Dict[str, Any]:
        src = Path(source_path)
        if not src.exists():
            return {"error": "file not found"}
        target = self.models_dir / src.name
        target.write_bytes(src.read_bytes())
        return {"success": True, "path": str(target), "type": src.suffix.lstrip(".") or "unknown"}

    async def hot_swap(self, model_name: str) -> Dict[str, Any]:
        target = self.models_dir / model_name
        if not target.exists():
            return {"error": "model not found"}
        return {"success": True, "active_model": model_name}
