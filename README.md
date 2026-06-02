# TERMINATOR I

**Advanced AI Inference System** — Sistema de inferencia extensible con soporte para avatares 3D, generación de vídeo en tiempo real, robótica, síntesis de voz y sistema de skills/Aureolas.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-terminatori-purple.svg)](https://pypi.org/project/terminatori/)

---

## Inicio Rápido

```bash
# Clonar
git clone https://github.com/yoqer/TERMINATORI.git
cd TERMINATORI

# Configurar
cp .env.example .env
# Editar .env con tus API keys

# Iniciar (local)
chmod +x start.sh && ./start.sh

# O con Docker
./start.sh docker
```

Panel web: `http://localhost:80`  
API docs: `http://localhost:8000/docs`

---

## Módulos

| Módulo | Descripción | Proveedores |
|--------|-------------|-------------|
| **Inferencia** | Motor LLM multi-backend | Ollama, OpenAI, Grok, Anthropic, llama.cpp |
| **Avatar** | Generación e importación 3D | Hunyuan3D (fal.ai), VRM, Live2D, GLB, FBX |
| **Vídeo** | Generación de vídeo | Runway Gen-4, SVD, Kling, fal.ai, MiniMax, Luma |
| **Voz** | TTS + STT | ElevenLabs, Grok TTS, Kokoro, OpenAI TTS, Whisper |
| **Robótica** | Control de robots | Isaac Lab, dimos/ROS2, Unitree G1, RoboClaw |
| **Skills** | Aureolas / plugins | 11 skills integradas + custom desde archivo |
| **Memoria** | Persistencia SQLite | Hechos, episodios, búsqueda semántica |
| **API** | REST + MCP + A2A | FastAPI, OpenAPI, WebSocket streaming |

---

## Skills / Aureolas

Sistema de plugins basado en la librería [Aureolas](https://github.com/yoqer/Aureolas):

| Skill | Categoría | Descripción |
|-------|-----------|-------------|
| AOrAlIA | AUREAS | Alineación de valores en el output |
| AureAlIA | AUREAS | Verificación de hechos + alineación |
| Mediapedia | Veridicas | Búsqueda en Wikipedia |
| IQuestLoop | AUREAS | Razonamiento iterativo multi-paso |
| ErrorInterpretar | Razonamiento | Corrección de errores de interpretación |
| Synthetic2 | Razonamiento | Datos sintéticos (Prime Intellect) |
| GenBit | Sesgos | Detección de sesgos de género |
| Safeguard | Seguridad | Filtro GPT OSS 120B-20B |
| Aardwark | Seguridad | Moderación OpenAI |

---

## API

```bash
# Inferencia
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hola", "model": "ollama/llama3.2"}'

# Generar avatar 3D
curl -X POST http://localhost:8000/api/v1/avatar/generate \
  -d '{"prompt": "A futuristic robot", "quality": "standard"}'

# Generar vídeo
curl -X POST http://localhost:8000/api/v1/video/generate \
  -d '{"prompt": "A robot walking", "provider": "runway", "duration": 5}'

# TTS
curl -X POST http://localhost:8000/api/v1/voice/synthesize \
  -d '{"text": "Hola mundo", "provider": "elevenlabs"}'

# Ejecutar skill
curl -X POST http://localhost:8000/api/v1/skills/execute \
  -d '{"skill": "Safeguard", "input": "texto a verificar"}'
```

---

## Despliegue

### Local
```bash
./start.sh local
```

### Docker
```bash
./start.sh docker
# Ver logs: docker compose logs -f
# Detener: docker compose down
```

### PyPI
```bash
pip install terminatori
terminatori --help
terminatori-server --port 8000
```

---

## Ecosistema

TERMINATOR I forma parte del ecosistema de **Gothan City**:

- [Terminator1](https://github.com/yoqer/Terminator1) — Motor Kokoro TTS
- [Aureolas](https://github.com/yoqer/Aureolas) — Sistema de skills/plugins
- [TerminaTodo](https://github.com/yoqer/TerminaTodo) — Gestión de almacenamiento
- [TenMiNaTor](https://github.com/yoqer/TenMiNaTor) — Framework de entrenamiento

---

## Licencia

MIT © Firmado: YoQer
