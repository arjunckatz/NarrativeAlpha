from fastapi.testclient import TestClient


def test_version(client: TestClient) -> None:
    response = client.get("/api/version")

    assert response.status_code == 200
    assert response.json()["name"] == "narrative-alpha-api"
    assert response.json()["version"] == "0.1.0"
    assert response.json()["environment"] == "development"
