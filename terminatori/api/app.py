"""
TERMINATORI API Server
======================
Servidor FastAPI con endpoints REST, MCP y A2A.
Compatible con OpenAI API format para integración directa con LM Studio, etc.
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "terminatori"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class InferRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


class SwitchModelRequest(BaseModel):
    model: str


class AvatarGenerateRequest(BaseModel):
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    type: str = "3d"
    quality: str = "standard"


class VideoGenerateRequest(BaseModel):
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    duration: int = 5
    provider: str = "runway"


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    provider: str = "openai"
    language: str = "es"
    speed: float = 1.0
    output_path: Optional[str] = None


class STTRequest(BaseModel):
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    provider: str = "whisper"
    language: Optional[str] = None


class SkillRequest(BaseModel):
    skill_name: Optional[str] = None
    skill: Optional[str] = None
    action: str = "execute"
    input: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class A2AMessage(BaseModel):
    """Mensaje del protocolo Agent-to-Agent de Google."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str = "TERMINATORI"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def _verify_token_factory(cfg):
    async def verify_token(authorization: Optional[str] = Header(None)):
        if cfg.api_secret and cfg.api_secret != "none":
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing Bearer token")
            token = authorization.split(" ", 1)[1]
            if token != cfg.api_secret:
                raise HTTPException(status_code=403, detail="Invalid token")

    return verify_token


async def _stream_openai_chunks(engine, req: ChatCompletionRequest):
    chunk_id = str(uuid.uuid4())
    async for token in engine.stream(
        prompt=req.messages[-1].content,
        session_id=req.session_id,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    ):
        chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{"delta": {"content": token}, "index": 0, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_infer_tokens(engine, req: InferRequest):
    async for token in engine.stream(
        prompt=req.prompt,
        session_id=req.session_id,
        system_prompt=req.system_prompt,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    ):
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield "data: [DONE]\n\n"


async def _list_models_impl(cfg) -> Dict[str, Any]:
    models: List[Dict[str, Any]] = []
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{cfg.ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("models", []):
                    models.append(
                        {
                            "id": f"ollama/{model['name']}",
                            "name": model["name"],
                            "provider": "ollama",
                            "size": model.get("size", 0),
                        }
                    )
    except Exception:
        logger.debug("No se pudo consultar Ollama para listar modelos", exc_info=True)

    models.extend(
        [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "grok/grok-2", "name": "Grok-2", "provider": "grok"},
            {"id": "grok/grok-3", "name": "Grok-3", "provider": "grok"},
            {
                "id": "anthropic/claude-3-5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "provider": "anthropic",
            },
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek"},
            {"id": "mistral/mistral-large", "name": "Mistral Large", "provider": "mistral"},
        ]
    )
    return {"models": models}


def create_app(engine=None, config=None) -> FastAPI:
    """Crea la aplicación FastAPI con todos los routers."""

    from terminatori.core.config import TerminatorIConfig
    from terminatori.skills.aureolas import SkillsManager
    from terminatori.voice.voice_manager import VoiceManager

    cfg = config or TerminatorIConfig()
    app = FastAPI(
        title="TERMINATORI API",
        description="Extensible AI Inference Engine - REST + MCP + A2A",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    if cfg.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    verify_token = None

    @app.on_event("startup")
    async def startup_event():
        nonlocal verify_token
        verify_token = await _verify_token_factory(cfg)

    def auth_dependency():
        async def _dependency(authorization: Optional[str] = Header(None)):
            if verify_token is None:
                validator = await _verify_token_factory(cfg)
                await validator(authorization)
            else:
                await verify_token(authorization)

        return _dependency

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0", "engine": "terminatori"}

    @app.get("/status")
    async def status():
        if engine:
            return engine.get_status()
        return {"running": False, "message": "Engine not attached"}

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")

        if req.stream:
            return StreamingResponse(_stream_openai_chunks(engine, req), media_type="text/event-stream")

        result = await engine.infer(
            prompt=req.messages[-1].content,
            session_id=req.session_id,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            tools=req.tools,
        )

        return {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {
                    "message": {"role": "assistant", "content": result.text},
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": result.tokens_used,
                "total_tokens": result.tokens_used,
            },
        }

    @app.post("/api/infer")
    @app.post("/api/v1/infer")
    async def infer(req: InferRequest, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        result = await engine.infer(
            prompt=req.prompt,
            session_id=req.session_id,
            system_prompt=req.system_prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return result.to_dict()

    @app.post("/api/stream")
    @app.post("/api/v1/stream")
    async def stream_infer(req: InferRequest, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        return StreamingResponse(_stream_infer_tokens(engine, req), media_type="text/event-stream")

    @app.post("/api/model/switch")
    async def switch_model(req: SwitchModelRequest, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        await engine.switch_model(req.model)
        return {"success": True, "model": req.model}

    @app.get("/api/models")
    async def list_models():
        return await _list_models_impl(cfg)

    @app.post("/api/sessions")
    async def create_session(system_prompt: Optional[str] = None, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        session_id = engine.new_session(system_prompt)
        return {"session_id": session_id}

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        history = engine.get_session_history(session_id)
        return {"session_id": session_id, "messages": [m.to_dict() for m in history]}

    @app.delete("/api/sessions/{session_id}")
    async def clear_session(session_id: str, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        engine.clear_session(session_id)
        return {"success": True}

    @app.post("/api/avatar/generate")
    @app.post("/api/v1/avatar/generate")
    async def generate_avatar(req: AvatarGenerateRequest, _=Depends(auth_dependency())):
        from terminatori.avatar.avatar_manager import AvatarManager

        mgr = AvatarManager(cfg)
        return await mgr.generate(
            prompt=req.prompt,
            image_url=req.image_url,
            avatar_type=req.type,
            quality=req.quality,
        )

    @app.get("/api/avatar/models")
    async def list_avatar_models():
        from terminatori.avatar.avatar_manager import AvatarManager

        mgr = AvatarManager(cfg)
        return {"models": mgr.list_local_models()}

    @app.post("/api/video/generate")
    @app.post("/api/v1/video/generate")
    async def generate_video(req: VideoGenerateRequest, _=Depends(auth_dependency())):
        from terminatori.video.video_manager import VideoManager

        mgr = VideoManager(cfg)
        return await mgr.generate(
            prompt=req.prompt,
            image_url=req.image_url,
            duration=req.duration,
            provider=req.provider,
        )

    @app.post("/api/tts")
    @app.post("/api/v1/voice/synthesize")
    async def text_to_speech(req: TTSRequest, _=Depends(auth_dependency())):
        mgr = VoiceManager(cfg)
        voice_id = None if req.voice in {"alloy", "default", ""} else req.voice
        return await mgr.synthesize(
            text=req.text,
            provider=req.provider,
            voice_id=voice_id,
            language=req.language,
            speed=req.speed,
            output_path=req.output_path,
        )

    @app.post("/api/stt")
    @app.post("/api/v1/voice/transcribe")
    async def speech_to_text(req: STTRequest, _=Depends(auth_dependency())):
        mgr = VoiceManager(cfg)
        audio_path = req.audio_path or req.audio_url
        if not audio_path:
            raise HTTPException(status_code=422, detail="audio_path or audio_url is required")
        return await mgr.transcribe(audio_path=audio_path, provider=req.provider, language=req.language)

    @app.get("/api/skills")
    async def list_skills():
        if engine and hasattr(engine, "list_plugins") and engine.list_plugins():
            return {"skills": engine.list_plugins()}
        return {"skills": SkillsManager().list_all()}

    @app.post("/api/skills/execute")
    @app.post("/api/v1/skills/execute")
    async def execute_skill(req: SkillRequest, _=Depends(auth_dependency())):
        skill_name = req.skill_name or req.skill
        if not skill_name:
            raise HTTPException(status_code=422, detail="skill_name or skill is required")

        if engine and hasattr(engine, "get_plugin"):
            plugin = engine.get_plugin(skill_name)
            if plugin and hasattr(plugin, req.action):
                result = await getattr(plugin, req.action)(**req.params)
                return {"result": result}

        mgr = SkillsManager(getattr(cfg, "skills_dir", None))
        if req.action != "execute":
            raise HTTPException(status_code=400, detail="Only 'execute' is supported by the built-in skills manager")

        if req.input is not None and "input_data" not in req.params and "text" not in req.params:
            result = await mgr.execute(skill_name, req.input, **req.params)
        else:
            payload = req.params.get("input_data") or req.params.get("text") or req.input or ""
            extra_params = dict(req.params)
            extra_params.pop("input_data", None)
            extra_params.pop("text", None)
            result = await mgr.execute(skill_name, payload, **extra_params)
        return {"result": result}

    @app.post("/api/robotics/command")
    async def robotics_command(command: Dict[str, Any], _=Depends(auth_dependency())):
        from terminatori.robotics.robot_manager import RobotManager

        mgr = RobotManager(cfg)
        return await mgr.execute_command(command)

    @app.get("/a2a/agent-card")
    async def a2a_agent_card():
        return {
            "name": cfg.a2a_agent_name,
            "description": cfg.a2a_agent_description,
            "version": "1.0.0",
            "capabilities": {
                "text": True,
                "streaming": True,
                "tools": cfg.enable_mcp,
                "multimodal": cfg.enable_avatar or cfg.enable_video,
                "voice": cfg.enable_tts or cfg.enable_stt,
                "robotics": cfg.enable_robotics,
            },
            "endpoints": {
                "infer": "/api/infer",
                "stream": "/api/stream",
                "chat": "/v1/chat/completions",
                "a2a": "/a2a/message",
            },
        }

    @app.post("/a2a/message")
    async def a2a_receive(msg: A2AMessage, _=Depends(auth_dependency())):
        if not engine:
            raise HTTPException(status_code=503, detail="Engine not started")
        result = await engine.infer(prompt=msg.content, session_id=msg.id)
        return {
            "id": str(uuid.uuid4()),
            "sender": "TERMINATORI",
            "recipient": msg.sender,
            "content": result.text,
            "in_reply_to": msg.id,
        }

    if cfg.enable_mcp:
        @app.get("/mcp/tools")
        async def mcp_list_tools():
            return {
                "tools": [
                    {
                        "name": "infer",
                        "description": "Run inference with the active model",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string"},
                                "session_id": {"type": "string"},
                            },
                            "required": ["prompt"],
                        },
                    },
                    {
                        "name": "switch_model",
                        "description": "Switch the active model",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"model": {"type": "string"}},
                            "required": ["model"],
                        },
                    },
                    {
                        "name": "list_models",
                        "description": "List available models",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            }

        @app.post("/mcp/call")
        async def mcp_call_tool(body: Dict[str, Any], _=Depends(auth_dependency())):
            tool_name = body.get("name")
            params = body.get("arguments", {})

            if tool_name == "infer":
                if not engine:
                    return {"error": "Engine not started"}
                result = await engine.infer(**params)
                return {"content": [{"type": "text", "text": result.text}]}
            if tool_name == "switch_model":
                if not engine:
                    return {"error": "Engine not started"}
                await engine.switch_model(params["model"])
                return {"content": [{"type": "text", "text": f"Switched to {params['model']}"}]}
            if tool_name == "list_models":
                models_resp = await _list_models_impl(cfg)
                return {"content": [{"type": "text", "text": json.dumps(models_resp)}]}
            return {"error": f"Unknown tool: {tool_name}"}

    candidate_panel_dirs = [
        Path(__file__).resolve().parents[2] / "panel",
        Path(__file__).resolve().parent.parent / "panel" / "static",
    ]
    panel_dir = next((path for path in candidate_panel_dirs if path.is_dir()), None)
    if panel_dir:
        app.mount("/panel", StaticFiles(directory=str(panel_dir), html=True), name="panel")

    @app.get("/")
    async def root():
        return {
            "name": "TERMINATORI",
            "version": "1.0.0",
            "docs": "/docs",
            "panel": "/panel" if panel_dir else None,
            "a2a": "/a2a/agent-card",
            "mcp": "/mcp/tools" if cfg.enable_mcp else None,
        }

    return app


app = create_app()


def main() -> None:
    from terminatori import TerminatorIConfig
    import uvicorn

    cfg = TerminatorIConfig()
    uvicorn.run(app, host=cfg.api_host, port=cfg.api_port)
