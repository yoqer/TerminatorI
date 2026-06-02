"""Gestor ligero de robótica para despliegue estándar y simulación local."""

from __future__ import annotations

from typing import Any, Dict, List


class RobotManager:
    def __init__(self, config=None):
        self.config = config
        self.framework = "sim"
        self.connected = False

    async def connect(self) -> Dict[str, Any]:
        self.connected = True
        return {"success": True, "framework": self.framework}

    def get_supported_frameworks(self) -> List[Dict[str, Any]]:
        return [
            {"id": "sim", "name": "Simulación local"},
            {"id": "isaac", "name": "NVIDIA Isaac"},
            {"id": "ros2", "name": "ROS2"},
            {"id": "unitree", "name": "Unitree"},
            {"id": "roboclaw", "name": "RoboClaw"},
        ]

    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected:
            await self.connect()

        cmd_type = command.get("type")
        if cmd_type == "move":
            return {"success": True, "action": "move", "command": command}
        if cmd_type == "stop":
            return {"success": True, "action": "stop"}
        if cmd_type == "natural_language":
            text = (command.get("text") or "").lower()
            if "para" in text or "stop" in text:
                return {"success": True, "action": "stop", "source": "nl"}
            return {"success": True, "action": "move", "source": "nl", "text": text}
        return {"error": f"Unknown command type: {cmd_type}"}
