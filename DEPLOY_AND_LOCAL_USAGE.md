# Despliegue y uso local

## Uso local

1. Copia `.env.example` a `.env` si quieres personalizar variables.
2. Ejecuta:

```bash
chmod +x start_local.sh
./start_local.sh
```

3. Abre:

- `http://localhost:8000/docs`
- `http://localhost:8000/health`
- `http://localhost:8000/panel`

## Producción / hosting común

Este paquete incluye varias opciones de despliegue habituales:

| Archivo | Uso |
|---|---|
| `Procfile` | Plataformas tipo Railway/Render/Heroku-like |
| `Dockerfile` | Contenedor estándar |
| `start_production.sh` | Arranque simple en VPS o hosting con shell |
| `requirements.txt` | Instalación directa de dependencias |
| `runtime.txt` | Referencia de versión de Python |

### Arranque manual en servidor Linux

```bash
pip install -r requirements.txt
uvicorn terminatori.api.app:app --host 0.0.0.0 --port 8000
```

### Variables de entorno más importantes

| Variable | Descripción |
|---|---|
| `PORT` | Puerto HTTP del servicio |
| `HOST` | Host de escucha |
| `TERMINATORI_MODEL` | Modelo por defecto |
| `TERMINATORI_API_SECRET` | Token Bearer opcional |
| `OPENAI_API_KEY` | Clave opcional para integraciones OpenAI |
| `OLLAMA_URL` | URL de Ollama si se usa localmente |

## Nota práctica

El paquete queda listo para funcionar **sin depender de un proveedor externo** gracias a respuestas fallback locales, aunque puedes conectarlo a proveedores reales configurando sus credenciales.
