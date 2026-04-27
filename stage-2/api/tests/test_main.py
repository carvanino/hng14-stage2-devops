import pytest
from fastapi.testclient import TestClient
import fakeredis


from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    fake_r = fakeredis.FakeRedis()
    monkeypatch.setattr("api.main.r", fake_r)
    return fake_r

def test_create_job(mock_redis):
    """Test that creating a job works and saves to Redis."""
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    job_id = data["job_id"]
    
    status = mock_redis.hget(f"job:{job_id}", "status")
    assert status is not None
    assert status.decode() == "queued"

def test_get_job_exists(mock_redis):
    """Test getting a job that already exists in Redis."""
    job_id = "test-job-123"
    mock_redis.hset(f"job:{job_id}", "status", "completed")
    
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["job_id"] == job_id
    assert data["status"] == "completed"

def test_get_job_not_found(mock_redis):
    """Test getting a job that does not exist."""
    response = client.get("/jobs/fake-id")
    assert response.status_code == 200
    data = response.json()
    
    assert "error" in data
    assert data["error"] == "not found"
