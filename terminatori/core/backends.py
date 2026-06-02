"""Backends mínimos de inferencia para despliegue local y hosting estándar."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional


class _BaseBackend:
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs

    async def close(self) -> None:
        return None

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        text = (
            f"Respuesta local de {self.__class__.__name__} para el modelo '{self.model}'. "
            f"Entrada recibida: {last_user}"
        )
        return {
            "text": text,
            "tokens_used": min(max(len(text.split()), 1), max_tokens),
            "metadata": {"temperature": temperature, "fallback": True, "tools": bool(tools)},
        }

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        response = await self.complete(messages=messages, temperature=temperature, max_tokens=max_tokens)
        for token in response["text"].split():
            yield token + " "


class OllamaBackend(_BaseBackend):
    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434"):
        super().__init__(model=model, base_url=base_url)
        self.base_url = base_url


class OpenAICompatibleBackend(_BaseBackend):
    def __init__(self, model: str, api_key: Optional[str] = None, base_url: str = "", provider: str = "openai-compatible"):
        super().__init__(model=model, api_key=api_key, base_url=base_url, provider=provider)
        self.api_key = api_key
        self.base_url = base_url
        self.provider = provider


class LlamaCppBackend(_BaseBackend):
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        super().__init__(model=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)
        self.model_path = model_path
