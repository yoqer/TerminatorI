"""Configuración principal de TERMINATORI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TerminatorIConfig:
    model: str = os.getenv("TERMINATORI_MODEL", "openai-compatible/demo")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    api_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    context_length: int = int(os.getenv("TERMINATORI_CONTEXT_LENGTH", "4096"))
    gpu_layers: int = int(os.getenv("TERMINATORI_GPU_LAYERS", "0"))
    system_prompt: str = os.getenv(
        "TERMINATORI_SYSTEM_PROMPT",
        "Eres TERMINATORI, un asistente técnico útil, claro y profesional.",
    )
    temperature: float = float(os.getenv("TERMINATORI_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("TERMINATORI_MAX_TOKENS", "1024"))
    enable_memory: bool = os.getenv("TERMINATORI_ENABLE_MEMORY", "true").lower() == "true"
    memory_db_path: str = os.getenv("TERMINATORI_MEMORY_DB", "/tmp/terminatori_memory.db")

    api_secret: str = os.getenv("TERMINATORI_API_SECRET", "none")
    enable_cors: bool = os.getenv("TERMINATORI_ENABLE_CORS", "true").lower() == "true"
    cors_origins: List[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("TERMINATORI_CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        or ["*"]
    )
    api_host: str = os.getenv("HOST", os.getenv("TERMINATORI_HOST", "0.0.0.0"))
    api_port: int = int(os.getenv("PORT", os.getenv("TERMINATORI_PORT", "8000")))

    enable_mcp: bool = os.getenv("TERMINATORI_ENABLE_MCP", "true").lower() == "true"
    enable_avatar: bool = os.getenv("TERMINATORI_ENABLE_AVATAR", "true").lower() == "true"
    enable_video: bool = os.getenv("TERMINATORI_ENABLE_VIDEO", "true").lower() == "true"
    enable_tts: bool = os.getenv("TERMINATORI_ENABLE_TTS", "true").lower() == "true"
    enable_stt: bool = os.getenv("TERMINATORI_ENABLE_STT", "true").lower() == "true"
    enable_robotics: bool = os.getenv("TERMINATORI_ENABLE_ROBOTICS", "true").lower() == "true"

    a2a_agent_name: str = os.getenv("TERMINATORI_A2A_NAME", "TERMINATORI")
    a2a_agent_description: str = os.getenv(
        "TERMINATORI_A2A_DESCRIPTION",
        "Agente de inferencia multimodal con API HTTP, skills y servicios auxiliares.",
    )
    skills_dir: str = os.getenv("TERMINATORI_SKILLS_DIR", "/tmp/terminatori_skills")
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
