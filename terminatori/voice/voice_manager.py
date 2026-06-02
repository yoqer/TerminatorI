"""
TERMINATORI Voice Manager
=========================
Síntesis de voz (TTS) y reconocimiento (STT) con múltiples proveedores:
- ElevenLabs (alta calidad, clonación de voz)
- Grok TTS (xAI)
- Kokoro TTS (local, basado en Terminator1/yoqer)
- OpenAI TTS (gpt-4o-audio-preview)
- Whisper (STT local y API)
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VoiceManager:
    """
    Gestiona síntesis y reconocimiento de voz.

    Proveedores TTS:
    - elevenlabs: ElevenLabs API (alta calidad, clonación)
    - grok: xAI Grok TTS
    - kokoro: Kokoro TTS local (yoqer/Terminator1)
    - openai: OpenAI TTS (tts-1, tts-1-hd)
    - coqui: Coqui TTS local (código abierto)

    Proveedores STT:
    - whisper: OpenAI Whisper (local o API)
    - deepgram: Deepgram API
    """

    TTS_PROVIDERS = {
        "elevenlabs": "ElevenLabs (alta calidad, clonación de voz)",
        "grok": "Grok TTS (xAI)",
        "kokoro": "Kokoro TTS (local, yoqer/Terminator1)",
        "openai": "OpenAI TTS (tts-1, tts-1-hd)",
        "coqui": "Coqui TTS (local, código abierto)",
        "gtts": "Google TTS (básico, gratuito)",
    }

    def __init__(self, config=None):
        self.config = config
        self.elevenlabs_key = getattr(config, "elevenlabs_api_key", None) or os.environ.get("ELEVENLABS_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.xai_key = os.environ.get("XAI_API_KEY")
        self.audio_dir = Path("~/.terminatori/audio").expanduser()
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(
        self,
        text: str,
        provider: str = "elevenlabs",
        voice_id: Optional[str] = None,
        language: str = "es",
        speed: float = 1.0,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sintetiza texto a voz.

        Args:
            text: Texto a sintetizar
            provider: Proveedor TTS
            voice_id: ID de voz (específico del proveedor)
            language: Código de idioma
            speed: Velocidad (0.5-2.0)
            output_path: Ruta de salida del archivo de audio

        Returns:
            Dict con audio_path, provider, duration y metadatos
        """
        generators = {
            "elevenlabs": self._tts_elevenlabs,
            "openai": self._tts_openai,
            "grok": self._tts_grok,
            "kokoro": self._tts_kokoro,
            "gtts": self._tts_gtts,
        }

        gen_fn = generators.get(provider)
        if not gen_fn:
            return {
                "error": f"Unknown TTS provider: {provider}",
                "available": list(self.TTS_PROVIDERS.keys()),
            }

        if not output_path:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_path = str(self.audio_dir / f"tts_{provider}_{text_hash}.mp3")

        return await gen_fn(
            text=text,
            voice_id=voice_id,
            language=language,
            speed=speed,
            output_path=output_path,
        )

    async def _tts_elevenlabs(
        self, text: str, voice_id=None, language="es", speed=1.0, output_path=None
    ) -> Dict[str, Any]:
        """Síntesis con ElevenLabs API."""
        if not self.elevenlabs_key:
            return {
                "error": "ELEVENLABS_API_KEY not configured",
                "docs": "https://elevenlabs.io/docs/api-reference",
            }

        # Voces predeterminadas por idioma
        default_voices = {
            "es": "pNInz6obpgDQGcFmaJgB",  # Adam (multilingual)
            "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "fr": "MF3mGyEYCl7XYWbV9V6O",  # Elli
        }
        vid = voice_id or default_voices.get(language, default_voices["en"])

        try:
            import httpx
            headers = {
                "xi-api-key": self.elevenlabs_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": speed,
                },
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(resp.content)

                return {
                    "success": True,
                    "audio_path": output_path,
                    "provider": "elevenlabs",
                    "voice_id": vid,
                    "model": "eleven_multilingual_v2",
                    "size_bytes": len(resp.content),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _tts_openai(
        self, text: str, voice_id=None, language="es", speed=1.0, output_path=None
    ) -> Dict[str, Any]:
        """Síntesis con OpenAI TTS."""
        if not self.openai_key:
            return {"error": "OPENAI_API_KEY not configured"}

        voice = voice_id or "nova"  # alloy, echo, fable, onyx, nova, shimmer
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "tts-1-hd",
                "input": text,
                "voice": voice,
                "speed": max(0.25, min(4.0, speed)),
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(resp.content)

                return {
                    "success": True,
                    "audio_path": output_path,
                    "provider": "openai",
                    "voice": voice,
                    "model": "tts-1-hd",
                }
        except Exception as e:
            return {"error": str(e)}

    async def _tts_grok(
        self, text: str, voice_id=None, language="es", speed=1.0, output_path=None
    ) -> Dict[str, Any]:
        """Síntesis con Grok TTS (xAI)."""
        if not self.xai_key:
            return {
                "error": "XAI_API_KEY not configured",
                "docs": "https://docs.x.ai/docs/guides/audio",
            }

        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.xai_key}",
                "Content-Type": "application/json",
            }
            # Grok TTS usa la API de audio de xAI
            payload = {
                "model": "grok-2-audio",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Say: {text}"},
                        ],
                    }
                ],
                "modalities": ["audio"],
                "audio": {"voice": voice_id or "aria", "format": "mp3"},
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                # Extraer audio base64
                import base64
                audio_b64 = data["choices"][0]["message"].get("audio", {}).get("data")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    return {
                        "success": True,
                        "audio_path": output_path,
                        "provider": "grok",
                        "model": "grok-2-audio",
                    }
                return {"error": "No audio in Grok response", "raw": data}

        except Exception as e:
            return {"error": str(e)}

    async def _tts_kokoro(
        self, text: str, voice_id=None, language="es", speed=1.0, output_path=None
    ) -> Dict[str, Any]:
        """
        Síntesis con Kokoro TTS local (yoqer/Terminator1).
        Requiere: pip install kokoro-onnx
        """
        try:
            from kokoro_onnx import Kokoro
            import soundfile as sf
            import numpy as np

            kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
            voice = voice_id or ("af_bella" if language == "en" else "es_maria")

            samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang=language)
            sf.write(output_path, samples, sample_rate)

            return {
                "success": True,
                "audio_path": output_path,
                "provider": "kokoro",
                "voice": voice,
                "sample_rate": sample_rate,
            }
        except ImportError:
            return {
                "error": "Kokoro not installed",
                "install": "pip install kokoro-onnx soundfile",
                "docs": "https://github.com/yoqer/Terminator1",
            }
        except Exception as e:
            return {"error": str(e)}

    async def _tts_gtts(
        self, text: str, voice_id=None, language="es", speed=1.0, output_path=None
    ) -> Dict[str, Any]:
        """Síntesis con Google TTS (gratuito, básico)."""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=(speed < 0.8))
            tts.save(output_path)
            return {
                "success": True,
                "audio_path": output_path,
                "provider": "gtts",
                "language": language,
            }
        except ImportError:
            return {"error": "gTTS not installed", "install": "pip install gtts"}
        except Exception as e:
            return {"error": str(e)}

    async def transcribe(
        self,
        audio_path: str,
        provider: str = "whisper",
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio a texto (STT).

        Args:
            audio_path: Ruta al archivo de audio
            provider: "whisper" | "deepgram"
            language: Código de idioma (None para detección automática)

        Returns:
            Dict con text, language, segments y metadatos
        """
        if provider == "whisper":
            return await self._stt_whisper(audio_path, language)
        elif provider == "deepgram":
            return await self._stt_deepgram(audio_path, language)
        else:
            return {"error": f"Unknown STT provider: {provider}"}

    async def _stt_whisper(self, audio_path: str, language=None) -> Dict[str, Any]:
        """Transcripción con Whisper (local o API)."""
        if self.openai_key:
            # Usar API de OpenAI
            try:
                import httpx
                headers = {"Authorization": f"Bearer {self.openai_key}"}
                with open(audio_path, "rb") as f:
                    files = {"file": (Path(audio_path).name, f, "audio/mpeg")}
                    data = {"model": "whisper-1"}
                    if language:
                        data["language"] = language

                    async with httpx.AsyncClient(timeout=120.0) as client:
                        resp = await client.post(
                            "https://api.openai.com/v1/audio/transcriptions",
                            headers=headers,
                            files=files,
                            data=data,
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        return {
                            "success": True,
                            "text": result.get("text"),
                            "provider": "whisper-api",
                        }
            except Exception as e:
                return {"error": str(e)}
        else:
            # Intentar Whisper local
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path, language=language)
                return {
                    "success": True,
                    "text": result["text"],
                    "language": result.get("language"),
                    "segments": result.get("segments", []),
                    "provider": "whisper-local",
                }
            except ImportError:
                return {
                    "error": "Whisper not installed and no OPENAI_API_KEY",
                    "install": "pip install openai-whisper",
                }

    async def _stt_deepgram(self, audio_path: str, language=None) -> Dict[str, Any]:
        """Transcripción con Deepgram API."""
        dg_key = os.environ.get("DEEPGRAM_API_KEY")
        if not dg_key:
            return {"error": "DEEPGRAM_API_KEY not configured"}

        try:
            import httpx
            headers = {
                "Authorization": f"Token {dg_key}",
                "Content-Type": "audio/mpeg",
            }
            params = {"model": "nova-3", "smart_format": "true"}
            if language:
                params["language"] = language

            with open(audio_path, "rb") as f:
                audio_data = f.read()

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    content=audio_data,
                )
                resp.raise_for_status()
                data = resp.json()
                transcript = (
                    data.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                return {
                    "success": True,
                    "text": transcript,
                    "provider": "deepgram",
                    "model": "nova-3",
                }
        except Exception as e:
            return {"error": str(e)}

    def list_providers(self) -> List[Dict[str, Any]]:
        """Lista los proveedores TTS disponibles con su estado."""
        return [
            {
                "id": pid,
                "name": name,
                "type": "tts",
                "configured": self._is_tts_configured(pid),
            }
            for pid, name in self.TTS_PROVIDERS.items()
        ]

    def _is_tts_configured(self, provider: str) -> bool:
        keys = {
            "elevenlabs": self.elevenlabs_key,
            "openai": self.openai_key,
            "grok": self.xai_key,
            "kokoro": True,  # Local, siempre disponible si instalado
            "gtts": True,    # Gratuito, siempre disponible
        }
        return bool(keys.get(provider, False))
