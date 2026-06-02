"""
TERMINATORI Core Engine
=======================
Motor principal de inferencia extensible.
Gestiona modelos, sesiones, plugins y comunicación entre módulos.
"""

import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Mensaje en una conversación."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InferenceResult:
    """Resultado de una inferencia."""

    text: str
    model: str
    session_id: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TerminatorI:
    """
    Motor principal de TERMINATORI.

    Ejemplo de uso:
        from terminatori import TerminatorI, TerminatorIConfig

        config = TerminatorIConfig(model="ollama/llama3.2")
        engine = TerminatorI(config)
        await engine.start()

        result = await engine.infer("Hola, ¿cómo estás?")
        print(result.text)
    """

    def __init__(self, config: Optional["TerminatorIConfig"] = None):
        from terminatori.core.config import TerminatorIConfig

        self.config = config or TerminatorIConfig()
        self.sessions: Dict[str, List[Message]] = {}
        self.plugins: Dict[str, Any] = {}
        self.active_model: Optional[str] = None
        self._running = False
        self._model_backend = None
        logger.info(f"TerminatorI initialized with model: {self.config.model}")

    async def start(self) -> None:
        """Inicializa el motor y carga el modelo configurado."""
        self._running = True
        await self._load_model(self.config.model)
        logger.info("TerminatorI engine started")

    async def stop(self) -> None:
        """Detiene el motor y libera recursos."""
        self._running = False
        if self._model_backend and hasattr(self._model_backend, "close"):
            await self._model_backend.close()
        logger.info("TerminatorI engine stopped")

    async def _load_model(self, model_id: str) -> None:
        """Carga un modelo por su identificador."""
        provider, _, model_name = model_id.partition("/")
        self.active_model = model_id

        if provider == "ollama":
            from terminatori.core.backends import OllamaBackend

            self._model_backend = OllamaBackend(
                model=model_name or "llama3.2",
                base_url=self.config.ollama_url,
            )
        elif provider in ("openai", "grok", "anthropic", "openai-compatible"):
            from terminatori.core.backends import OpenAICompatibleBackend

            self._model_backend = OpenAICompatibleBackend(
                model=model_name,
                api_key=self.config.api_key,
                base_url=self.config.api_base_url,
                provider=provider,
            )
        elif provider == "llamacpp":
            from terminatori.core.backends import LlamaCppBackend

            self._model_backend = LlamaCppBackend(
                model_path=model_name,
                n_ctx=self.config.context_length,
                n_gpu_layers=self.config.gpu_layers,
            )
        else:
            from terminatori.core.backends import OllamaBackend

            self._model_backend = OllamaBackend(model=model_id, base_url=self.config.ollama_url)

        logger.info(f"Model loaded: {model_id} via {provider}")

    def new_session(self, system_prompt: Optional[str] = None) -> str:
        """Crea una nueva sesión de conversación."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        if system_prompt or self.config.system_prompt:
            prompt = system_prompt or self.config.system_prompt
            self.sessions[session_id].append(Message(role="system", content=prompt))
        return session_id

    def _ensure_session(self, session_id: Optional[str], system_prompt: Optional[str] = None) -> str:
        """Garantiza que exista una sesión válida y devuelve su ID."""
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
                if system_prompt or self.config.system_prompt:
                    prompt = system_prompt or self.config.system_prompt
                    self.sessions[session_id].append(Message(role="system", content=prompt))
            return session_id
        return self.new_session(system_prompt)

    def get_session_history(self, session_id: str) -> List[Message]:
        """Devuelve el historial de mensajes de una sesión."""
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Limpia el historial de una sesión."""
        if session_id in self.sessions:
            history = self.sessions[session_id]
            system_msgs = [m for m in history if m.role == "system"]
            self.sessions[session_id] = system_msgs

    async def infer(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> InferenceResult:
        """Realiza una inferencia con el modelo activo."""
        if not self._model_backend:
            raise RuntimeError("Engine not started. Call await engine.start() first.")

        start_time = time.time()
        session_id = self._ensure_session(session_id, system_prompt)

        user_msg = Message(role="user", content=prompt)
        self.sessions[session_id].append(user_msg)
        messages = [m.to_dict() for m in self.sessions[session_id]]

        try:
            response = await self._model_backend.complete(
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                tools=tools,
            )
        except Exception as e:
            logger.error(f"Inference error: {e}")
            raise

        assistant_msg = Message(role="assistant", content=response["text"])
        self.sessions[session_id].append(assistant_msg)

        if self.config.enable_memory:
            await self._save_to_memory(session_id, user_msg, assistant_msg)

        latency = (time.time() - start_time) * 1000

        return InferenceResult(
            text=response["text"],
            model=self.active_model or "unknown",
            session_id=session_id,
            tokens_used=response.get("tokens_used", 0),
            latency_ms=latency,
            metadata=response.get("metadata", {}),
        )

    async def stream(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Genera tokens en streaming."""
        if not self._model_backend:
            raise RuntimeError("Engine not started.")

        session_id = self._ensure_session(session_id, system_prompt)

        user_msg = Message(role="user", content=prompt)
        self.sessions[session_id].append(user_msg)
        messages = [m.to_dict() for m in self.sessions[session_id]]

        full_response = ""
        async for chunk in self._model_backend.stream(
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        ):
            full_response += chunk
            yield chunk

        assistant_msg = Message(role="assistant", content=full_response)
        self.sessions[session_id].append(assistant_msg)

    async def _save_to_memory(self, session_id: str, user_msg: Message, assistant_msg: Message) -> None:
        """Guarda el intercambio en memoria persistente."""
        try:
            from terminatori.memory.memory_manager import MemoryManager

            mem = MemoryManager(self.config.memory_db_path)
            await mem.save_exchange(
                session_id=session_id,
                user_content=user_msg.content,
                assistant_content=assistant_msg.content,
            )
        except Exception as e:
            logger.warning(f"Memory save failed: {e}")

    def load_plugin(self, plugin_name: str, plugin_instance: Any) -> None:
        """Registra un plugin/skill en el motor."""
        self.plugins[plugin_name] = plugin_instance
        logger.info(f"Plugin loaded: {plugin_name}")

    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Obtiene un plugin registrado."""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """Lista los plugins registrados."""
        return list(self.plugins.keys())

    async def switch_model(self, model_id: str) -> None:
        """Cambia el modelo activo en caliente."""
        logger.info(f"Switching model from {self.active_model} to {model_id}")
        await self._load_model(model_id)

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado actual del motor."""
        return {
            "running": self._running,
            "active_model": self.active_model,
            "active_sessions": len(self.sessions),
            "loaded_plugins": self.list_plugins(),
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "enable_memory": self.config.enable_memory,
            },
        }
