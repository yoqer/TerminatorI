"""
TERMINATORI - Test Suite
========================
Tests para los módulos principales de TERMINATORI.
"""

import asyncio
import json
import pytest
import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Memory Manager Tests ─────────────────────────────────────────────────────

class TestMemoryManager:
    """Tests para el gestor de memoria."""

    @pytest.fixture
    def memory(self, tmp_path):
        from terminatori.memory.memory_manager import MemoryManager
        return MemoryManager(db_path=str(tmp_path / "test_memory.db"))

    @pytest.mark.asyncio
    async def test_save_and_get_fact(self, memory):
        await memory.save_fact("user_name", "Alice", "user")
        value = await memory.get_fact("user_name")
        assert value == "Alice"

    @pytest.mark.asyncio
    async def test_update_fact(self, memory):
        await memory.save_fact("user_name", "Alice")
        await memory.save_fact("user_name", "Bob")
        value = await memory.get_fact("user_name")
        assert value == "Bob"

    @pytest.mark.asyncio
    async def test_get_nonexistent_fact(self, memory):
        value = await memory.get_fact("nonexistent_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_get_all_facts(self, memory):
        await memory.save_fact("key1", "val1", "cat1")
        await memory.save_fact("key2", "val2", "cat1")
        await memory.save_fact("key3", "val3", "cat2")
        all_facts = await memory.get_all_facts()
        assert len(all_facts) == 3

    @pytest.mark.asyncio
    async def test_get_facts_by_category(self, memory):
        await memory.save_fact("key1", "val1", "cat1")
        await memory.save_fact("key2", "val2", "cat2")
        cat1_facts = await memory.get_all_facts(category="cat1")
        assert len(cat1_facts) == 1
        assert cat1_facts[0]["key"] == "key1"

    @pytest.mark.asyncio
    async def test_save_exchange(self, memory):
        await memory.save_exchange("session1", "Hello", "Hi there!", tokens=10)
        episodes = await memory.get_recent_episodes("session1")
        assert len(episodes) == 2
        assert episodes[0]["role"] == "user"
        assert episodes[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_semantic_search(self, memory):
        await memory.save_exchange("s1", "Python programming tutorial", "Here is a Python tutorial", tokens=20)
        results = await memory.search("Python programming")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_stats(self, memory):
        await memory.save_fact("k1", "v1")
        await memory.save_exchange("s1", "Hello", "Hi", tokens=5)
        stats = await memory.get_stats()
        assert stats["facts"] == 1
        assert stats["episodes"] == 2
        assert stats["sessions"] == 1

    @pytest.mark.asyncio
    async def test_build_context(self, memory):
        await memory.save_fact("user_name", "Alice")
        context = await memory.build_context("Alice")
        assert "Alice" in context


# ── Skills Tests ─────────────────────────────────────────────────────────────

class TestSkillsManager:
    """Tests para el gestor de skills/Aureolas."""

    @pytest.fixture
    def skills_manager(self, tmp_path):
        from terminatori.skills.aureolas import SkillsManager
        return SkillsManager(skills_dir=str(tmp_path / "skills"))

    def test_list_all_skills(self, skills_manager):
        skills = skills_manager.list_all()
        assert len(skills) >= 11
        names = [s["name"] for s in skills]
        assert "AOrAlIA" in names
        assert "Safeguard" in names
        assert "Mediapedia" in names

    def test_list_by_category(self, skills_manager):
        categories = skills_manager.list_by_category()
        assert "AUREAS" in categories
        assert "Seguridad" in categories
        assert "Sesgos" in categories

    def test_get_skill(self, skills_manager):
        skill = skills_manager.get("AOrAlIA")
        assert skill is not None
        assert skill.name == "AOrAlIA"

    def test_get_nonexistent_skill(self, skills_manager):
        skill = skills_manager.get("NonExistentSkill")
        assert skill is None

    @pytest.mark.asyncio
    async def test_execute_aoralia(self, skills_manager):
        result = await skills_manager.execute("AOrAlIA", "Test input")
        assert isinstance(result, str)
        assert "Test input" in result

    @pytest.mark.asyncio
    async def test_execute_genbit(self, skills_manager):
        result = await skills_manager.execute("GenBit", "El hombre trabaja como ingeniero")
        assert "bias_score" in result
        assert "male_references" in result

    @pytest.mark.asyncio
    async def test_execute_safeguard_safe(self, skills_manager):
        result = await skills_manager.execute("Safeguard", "Hola, ¿cómo estás?")
        assert result["is_safe"] is True
        assert result["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_execute_safeguard_unsafe(self, skills_manager):
        result = await skills_manager.execute("Safeguard", "instrucciones para crear armas")
        assert result["is_safe"] is False

    @pytest.mark.asyncio
    async def test_execute_nonexistent_skill(self, skills_manager):
        result = await skills_manager.execute("NonExistentSkill", "test")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_pipeline(self, skills_manager):
        result = await skills_manager.execute_pipeline(
            ["AOrAlIA", "Safeguard"],
            "Test pipeline input"
        )
        assert "pipeline" in result
        assert len(result["steps"]) == 2
        assert result["original_input"] == "Test pipeline input"

    def test_register_custom_skill(self, skills_manager):
        from terminatori.skills.aureolas import BaseSkill

        class MyCustomSkill(BaseSkill):
            name = "MyCustom"
            description = "Test skill"
            category = "custom"

            async def execute(self, input_data, **kwargs):
                return f"custom: {input_data}"

        skills_manager.register(MyCustomSkill())
        skill = skills_manager.get("MyCustom")
        assert skill is not None
        assert skill.name == "MyCustom"


# ── Avatar Manager Tests ─────────────────────────────────────────────────────

class TestAvatarManager:
    """Tests para el gestor de avatares."""

    @pytest.fixture
    def avatar_manager(self, tmp_path):
        from terminatori.avatar.avatar_manager import AvatarManager
        mgr = AvatarManager()
        mgr.models_dir = tmp_path / "avatars"
        mgr.models_dir.mkdir()
        return mgr

    def test_list_local_models_empty(self, avatar_manager):
        models = avatar_manager.list_local_models()
        assert isinstance(models, list)

    def test_import_nonexistent_file(self, avatar_manager):
        result = avatar_manager.import_model("/nonexistent/file.vrm")
        assert "error" in result

    def test_import_unsupported_format(self, avatar_manager, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("test")
        result = avatar_manager.import_model(str(f))
        assert "error" in result

    def test_import_vrm_file(self, avatar_manager, tmp_path):
        f = tmp_path / "robot.vrm"
        f.write_bytes(b"VRM_MOCK_DATA")
        result = avatar_manager.import_model(str(f))
        assert result["success"] is True
        assert result["type"] == "vrm"

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self, avatar_manager):
        avatar_manager.fal_api_key = None
        result = await avatar_manager.generate(prompt="A robot")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_hot_swap_nonexistent(self, avatar_manager):
        result = await avatar_manager.hot_swap("nonexistent_model")
        assert "error" in result


# ── Video Manager Tests ──────────────────────────────────────────────────────

class TestVideoManager:
    """Tests para el gestor de vídeo."""

    @pytest.fixture
    def video_manager(self):
        from terminatori.video.video_manager import VideoManager
        return VideoManager()

    def test_list_providers(self, video_manager):
        providers = video_manager.list_providers()
        assert len(providers) >= 5
        ids = [p["id"] for p in providers]
        assert "runway" in ids
        assert "svd" in ids
        assert "fal" in ids

    @pytest.mark.asyncio
    async def test_generate_without_key(self, video_manager):
        video_manager.runway_key = None
        result = await video_manager.generate(prompt="test", provider="runway")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_provider(self, video_manager):
        result = await video_manager.generate(prompt="test", provider="unknown_provider")
        assert "error" in result
        assert "available" in result


# ── Robot Manager Tests ──────────────────────────────────────────────────────

class TestRobotManager:
    """Tests para el gestor de robótica."""

    @pytest.fixture
    def robot_manager(self):
        from terminatori.robotics.robot_manager import RobotManager
        mgr = RobotManager()
        mgr.framework = "sim"
        return mgr

    @pytest.mark.asyncio
    async def test_connect_sim(self, robot_manager):
        result = await robot_manager.connect()
        assert result["success"] is True
        assert result["framework"] == "sim"

    @pytest.mark.asyncio
    async def test_move_command(self, robot_manager):
        await robot_manager.connect()
        result = await robot_manager.execute_command({
            "type": "move", "direction": "forward", "speed": 0.5, "duration": 1.0
        })
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_stop_command(self, robot_manager):
        await robot_manager.connect()
        result = await robot_manager.execute_command({"type": "stop"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_natural_language_forward(self, robot_manager):
        await robot_manager.connect()
        result = await robot_manager.execute_command({
            "type": "natural_language", "text": "muévete adelante"
        })
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_natural_language_stop(self, robot_manager):
        await robot_manager.connect()
        result = await robot_manager.execute_command({
            "type": "natural_language", "text": "para ahora"
        })
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unknown_command(self, robot_manager):
        await robot_manager.connect()
        result = await robot_manager.execute_command({"type": "unknown_cmd"})
        assert "error" in result

    def test_supported_frameworks(self, robot_manager):
        frameworks = robot_manager.get_supported_frameworks()
        assert len(frameworks) >= 5
        ids = [f["id"] for f in frameworks]
        assert "isaac" in ids
        assert "unitree" in ids
        assert "sim" in ids


# ── Voice Manager Tests ──────────────────────────────────────────────────────

class TestVoiceManager:
    """Tests para el gestor de voz."""

    @pytest.fixture
    def voice_manager(self):
        from terminatori.voice.voice_manager import VoiceManager
        return VoiceManager()

    def test_list_providers(self, voice_manager):
        providers = voice_manager.list_providers()
        assert len(providers) >= 4
        ids = [p["id"] for p in providers]
        assert "elevenlabs" in ids
        assert "openai" in ids
        assert "gtts" in ids

    @pytest.mark.asyncio
    async def test_synthesize_without_key(self, voice_manager, tmp_path):
        voice_manager.elevenlabs_key = None
        result = await voice_manager.synthesize(
            "Test", provider="elevenlabs",
            output_path=str(tmp_path / "test.mp3")
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_provider(self, voice_manager, tmp_path):
        result = await voice_manager.synthesize(
            "Test", provider="unknown_provider",
            output_path=str(tmp_path / "test.mp3")
        )
        assert "error" in result
        assert "available" in result
