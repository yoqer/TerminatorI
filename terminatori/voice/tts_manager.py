"""Wrapper de compatibilidad para síntesis de voz."""

from terminatori.voice.voice_manager import VoiceManager


class TTSManager(VoiceManager):
    """Alias retrocompatible de VoiceManager para TTS."""

    pass
