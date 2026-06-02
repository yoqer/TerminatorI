"""Sistema ligero de skills para el paquete listo para despliegue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BaseSkill:
    name: str
    description: str
    category: str

    async def execute(self, input_data: str, **kwargs):
        return {"skill": self.name, "input": input_data, "message": self.description}


class EchoSkill(BaseSkill):
    def __init__(self):
        super().__init__(name="AOrAlIA", description="Reformula y devuelve el contenido de entrada.", category="AUREAS")

    async def execute(self, input_data: str, **kwargs):
        return f"AOrAlIA procesó: {input_data}"


class SafeguardSkill(BaseSkill):
    def __init__(self):
        super().__init__(name="Safeguard", description="Chequeo simple de seguridad de texto.", category="Seguridad")

    async def execute(self, input_data: str, **kwargs):
        lowered = input_data.lower()
        risk_terms = ["arma", "explosivo", "malware", "hackear"]
        unsafe = any(term in lowered for term in risk_terms)
        return {"is_safe": not unsafe, "risk_level": "low" if not unsafe else "high", "input": input_data}


class MediapediaSkill(BaseSkill):
    def __init__(self):
        super().__init__(name="Mediapedia", description="Devuelve una ficha rápida del tema consultado.", category="Veridicas")

    async def execute(self, input_data: str, **kwargs):
        return {"topic": input_data, "summary": f"Resumen local disponible para: {input_data}"}


class SkillsManager:
    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir
        self._registry: Dict[str, BaseSkill] = {}
        self.register(EchoSkill())
        self.register(SafeguardSkill())
        self.register(MediapediaSkill())

    def register(self, skill: BaseSkill) -> None:
        self._registry[skill.name] = skill

    def get(self, name: str) -> Optional[BaseSkill]:
        return self._registry.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        return [
            {"name": skill.name, "description": skill.description, "category": skill.category}
            for skill in self._registry.values()
        ]

    def list_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in self.list_all():
            grouped.setdefault(item["category"], []).append(item)
        return grouped

    async def execute(self, name: str, input_data: str, **kwargs):
        skill = self.get(name)
        if not skill:
            return {"error": f"Skill not found: {name}"}
        return await skill.execute(input_data, **kwargs)

    async def execute_pipeline(self, pipeline: List[str], input_data: str):
        steps = []
        current = input_data
        for name in pipeline:
            result = await self.execute(name, current)
            steps.append({"skill": name, "result": result})
            if isinstance(result, str):
                current = result
        return {"pipeline": pipeline, "original_input": input_data, "steps": steps}
