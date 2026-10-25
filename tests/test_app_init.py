def test_app_creation(app):
    """Verifies that the application initializes successfully with test settings."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_health_endpoint(client):
    """Tests the /api/health monitoring probe."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "gemini_configured" in data


def test_dashboard_renders(client):
    """Verifies that the dashboard route renders with seeded metrics."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"AI Engineering Lab" in resp.data
    assert b"Curriculum Modules" in resp.data


def test_search_endpoint(client):
    """Tests the global search API."""
    resp = client.get("/search?q=Prompt&format=json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "lessons" in data
    assert len(data["lessons"]) > 0
