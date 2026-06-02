"""
TERMINATORI - Extensible AI Inference Engine
============================================
Sistema de inferencia extensible con soporte para:
- Modelos LLM locales (Ollama, llama.cpp) y en nube (OpenAI, Grok, Anthropic)
- Avatares 3D (Live2D, Hunyuan3D, importación de formatos)
- Generación de vídeo en tiempo real (Runway, SVD, Kling)
- Robótica (Isaac Lab, dimos, Unitree G1, RoboClaw)
- Sistema de skills/plugins (Aureolas, SafeGuard, MCP Market)
- API REST + MCP server + A2A endpoint
- Panel web HTML de control
- Sincronización offline/online (integración TerminaTodo)

Repositorio: https://github.com/yoqer/TERMINATORI
PyPI: pip install terminatori
"""

__version__ = "1.0.0"
__author__ = "yoqer"
__license__ = "MIT"
__description__ = "Advanced AI Inference System with Avatars, Video, Robotics and Skills"

try:
    from terminatori.core.engine import TerminatorI
    from terminatori.core.config import TerminatorIConfig

    # Alias de compatibilidad hacia atrás.
    TerminatoriEngine = TerminatorI
    TerminatoriConfig = TerminatorIConfig

    __all__ = [
        "TerminatorI",
        "TerminatorIConfig",
        "TerminatoriEngine",
        "TerminatoriConfig",
        "__version__",
    ]
except ImportError:
    __all__ = ["__version__"]
