"""Wrapper de compatibilidad para reconocimiento de voz."""

from terminatori.voice.voice_manager import VoiceManager


class STTManager(VoiceManager):
    """Alias retrocompatible de VoiceManager para STT."""

    pass
