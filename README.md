# App Terminator I · Rama `local`

**App Terminator I** en la rama **`local`** es una variante preparada para **uso local**, **pruebas funcionales** y **despliegue en hosting web estándar** mediante un servidor **FastAPI/ASGI**. Esta rama sustituye el contenedor original empaquetado en RAR por una estructura Python utilizable directamente, con scripts de arranque, configuración base y una interfaz web mínima para comprobación rápida del servicio.

## Propósito de esta rama

Esta rama está orientada a un escenario práctico de ejecución. El proyecto queda listo para levantarse en un equipo local, un VPS, un contenedor Docker o una plataforma compatible con aplicaciones Python que expongan un proceso web. Además, incluye respuestas de respaldo locales para que el sistema pueda arrancar incluso sin un proveedor externo configurado, lo que facilita validación técnica, integración inicial y desarrollo incremental.

| Elemento | Estado en la rama `local` | Observación |
|---|---|---|
| API HTTP | Disponible | Basada en FastAPI |
| Panel web mínimo | Disponible | Servido desde `/panel` |
| Documentación OpenAPI | Disponible | Visible en `/docs` |
| Arranque local | Disponible | Mediante `start_local.sh` |
| Arranque para servidor | Disponible | Mediante `start_production.sh` |
| Despliegue con Docker | Disponible | Incluye `Dockerfile` |
| Despliegue tipo PaaS | Disponible | Incluye `Procfile` |
| Variables de entorno base | Disponible | Incluye `.env.example` |
| Respuesta fallback local | Disponible | Permite pruebas sin proveedor real |

## Estructura principal del proyecto

El repositorio en esta rama se organiza alrededor del paquete `terminatori`, que concentra la API, el motor principal, módulos auxiliares y capacidades complementarias. También se incluyen archivos de despliegue y pruebas básicas para verificar el funcionamiento general.

| Ruta | Función |
|---|---|
| `terminatori/api/app.py` | Servidor FastAPI y punto de entrada ASGI |
| `terminatori/core/engine.py` | Motor principal de inferencia y sesiones |
| `terminatori/core/config.py` | Configuración por entorno |
| `terminatori/core/backends.py` | Backends mínimos y fallback local |
| `terminatori/voice/` | Gestión de TTS y STT |
| `terminatori/avatar/` | Gestión base de avatar |
| `terminatori/video/` | Gestión base de vídeo |
| `terminatori/robotics/` | Gestión base de robótica simulada |
| `terminatori/skills/` | Skills/Aureolas incluidas |
| `terminatori/memory/` | Persistencia ligera en SQLite |
| `terminatori/panel/static/` | Panel HTML mínimo |
| `tests/` | Pruebas existentes del proyecto |
| `DEPLOY_AND_LOCAL_USAGE.md` | Guía breve de despliegue |

## Inicio rápido en local

La forma más simple de usar esta rama consiste en crear el entorno virtual, instalar dependencias y arrancar el servidor en modo desarrollo. Para ello, basta con ejecutar el script incluido.

```bash
git clone -b local https://github.com/yoqer/TerminatorI.git
cd TerminatorI
cp .env.example .env
chmod +x start_local.sh
./start_local.sh
```

Una vez iniciado el servicio, las rutas más útiles son las siguientes.

| URL | Uso |
|---|---|
| `http://localhost:8000/health` | Comprobación de salud del servicio |
| `http://localhost:8000/docs` | Documentación interactiva OpenAPI |
| `http://localhost:8000/panel` | Panel web mínimo |
| `http://localhost:8000/api/models` | Modelos expuestos por la API |
| `http://localhost:8000/api/skills` | Skills disponibles |

## Despliegue en hosting estándar

La rama `local` también se ha preparado para despliegues sencillos en entornos habituales. Si el proveedor soporta aplicaciones Python con proceso web, puede usarse el `Procfile`. Si el entorno es un VPS o una máquina Linux propia, puede utilizarse el script de producción o un comando `uvicorn` directo. Si se prefiere contenedor, el repositorio incorpora un `Dockerfile` funcional.

| Archivo | Escenario recomendado |
|---|---|
| `start_production.sh` | VPS, servidor Linux o shell remoto |
| `Procfile` | Plataformas tipo Render, Railway o similares |
| `Dockerfile` | Contenedor Docker estándar |
| `requirements.txt` | Instalación manual de dependencias |
| `runtime.txt` | Referencia de versión Python |

Ejemplo de arranque manual en servidor:

```bash
pip install -r requirements.txt
uvicorn terminatori.api.app:app --host 0.0.0.0 --port 8000
```

## Variables de entorno principales

La configuración se resuelve a través de variables de entorno. El archivo `.env.example` ofrece una base suficiente para empezar. Las variables más importantes son las siguientes.

| Variable | Descripción |
|---|---|
| `HOST` | Dirección de escucha del servidor |
| `PORT` | Puerto HTTP del servicio |
| `TERMINATORI_MODEL` | Modelo por defecto del motor |
| `TERMINATORI_API_SECRET` | Token Bearer opcional para proteger endpoints |
| `TERMINATORI_ENABLE_CORS` | Activación de CORS |
| `TERMINATORI_CORS_ORIGINS` | Orígenes permitidos |
| `OPENAI_API_KEY` | Clave opcional para integraciones OpenAI |
| `OPENAI_BASE_URL` | URL base del proveedor OpenAI-compatible |
| `OLLAMA_URL` | URL de Ollama para uso local |
| `ELEVENLABS_API_KEY` | Clave opcional para TTS externo |

## API disponible en esta rama

Esta rama ofrece una API unificada para pruebas, desarrollo e integración. Las rutas incluidas cubren inferencia, sesiones, voz, skills, modelo activo, A2A y un punto de entrada compatible con estilo OpenAI para chat.

| Grupo | Rutas principales |
|---|---|
| Salud | `/health`, `/status` |
| Inferencia | `/api/infer`, `/api/v1/infer`, `/api/stream` |
| Chat | `/v1/chat/completions` |
| Modelos | `/api/models`, `/api/model/switch` |
| Sesiones | `/api/sessions`, `/api/sessions/{session_id}` |
| Voz | `/api/tts`, `/api/stt`, `/api/v1/voice/synthesize`, `/api/v1/voice/transcribe` |
| Skills | `/api/skills`, `/api/skills/execute` |
| Avatar | `/api/avatar/generate` |
| Vídeo | `/api/video/generate` |
| Robótica | `/api/robotics/command` |
| A2A | `/a2a/agent-card`, `/a2a/message` |
| MCP | `/mcp/tools`, `/mcp/call` |
| Panel | `/panel` |

Ejemplos rápidos:

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hola, AppTerminatorI"}'
```

```bash
curl -X POST http://localhost:8000/api/v1/skills/execute \
  -H "Content-Type: application/json" \
  -d '{"skill": "Safeguard", "input": "revisa este contenido"}'
```

## Sobre el motor local y los fallbacks

Para esta rama se ha priorizado la **operatividad inmediata**. Por ello, el motor dispone de backends mínimos y una respuesta local de respaldo cuando no hay proveedor externo configurado. Esto permite validar arranque, sesiones, rutas, integración HTTP y cableado interno del proyecto sin bloquear la puesta en marcha por credenciales o servicios de terceros.

Este enfoque es útil en desarrollo y en despliegues de demostración. Si se quiere comportamiento productivo real con inferencia remota o local avanzada, bastará con conectar proveedores externos o ampliar los backends existentes.

## Skills, memoria y extensibilidad

El proyecto mantiene una estructura preparada para crecer. La rama `local` incluye un conjunto base de skills/Aureolas, una capa de memoria SQLite y gestores auxiliares para avatar, vídeo y robótica. En esta versión, algunos de esos módulos funcionan como implementaciones ligeras o placeholders útiles para pruebas, integración incremental y futura sustitución por adaptadores reales.

| Área | Situación actual | Evolución recomendada |
|---|---|---|
| Skills | Base funcional | Añadir catálogo ampliado y registro dinámico |
| Memoria | SQLite ligera | Añadir embeddings, ranking y búsqueda semántica avanzada |
| Voz | Base funcional | Completar proveedores y persistencia de ficheros |
| Avatar/Vídeo | Placeholder funcional | Integrar proveedores reales y colas de trabajo |
| Robótica | Simulación básica | Añadir conectores hardware o ROS2 |

## Integración con TenMiNaTor y opción de corrección de sesgos

Dentro del ecosistema relacionado, la referencia correcta del framework de entrenamiento es **TenMiNaTor**. Si este repositorio evoluciona hacia una integración más profunda con dicho framework, resulta recomendable incorporar una opción de **corrección de sesgos** aplicable tanto sobre capas intermedias como sobre la inferencia final, siguiendo un enfoque de *steering* configurable. En esta rama, esa funcionalidad se considera una ampliación futura razonable y no una capacidad cerrada del estado actual. -Existe ya en [TerMiNaTor 2](https://github.com/yoqer/Terminator-2)

## Recomendaciones para trabajo posterior

La rama `local` deja una base utilizable, pero su valor aumenta mucho si se continúa con una fase adicional de endurecimiento técnico. En particular, conviene ampliar la suite de pruebas, conectar proveedores reales, reforzar autenticación y añadir persistencia estructurada para resultados multimedia.

| Prioridad | Recomendación |
|---|---|
| Alta | Añadir pruebas de integración para todos los endpoints críticos |
| Alta | Conectar backends reales de inferencia y voz |
| Media | Incorporar colas de tareas para procesos pesados |
| Media | Mejorar la seguridad de producción y gestión de secretos |
| Media | Añadir logging estructurado y observabilidad |
| Baja | Sustituir el panel mínimo por una interfaz operativa más completa |

## Licencia

El proyecto se distribuye bajo licencia **MIT** según la configuración actual del paquete.

## Autoría

Repositorio original: **yoqer**.  
Adaptación técnica de la rama **`local`** y documentación final: **Manus AI**.
