from fastapi.testclient import TestClient

from terminatori.api.app import create_app

app = create_app()
client = TestClient(app)

checks = []
for method, path, expected in [
    ("get", "/health", 200),
    ("get", "/", 200),
    ("get", "/api/models", 200),
    ("get", "/api/skills", 200),
    ("get", "/a2a/agent-card", 200),
]:
    response = getattr(client, method)(path)
    checks.append((path, response.status_code, response.json()))
    assert response.status_code == expected, (path, response.status_code, response.text)

root = client.get("/").json()
assert root["docs"] == "/docs"
assert "a2a" in root

skills = client.get("/api/skills").json()
assert "skills" in skills
assert isinstance(skills["skills"], list)
assert len(skills["skills"]) >= 1

print("SMOKE_OK")
for path, status, payload in checks:
    print(path, status, list(payload)[:5])
