from fastapi.testclient import TestClient

from breachwatch.api import app


client = TestClient(app)


def test_breach_check_returns_risk_and_mitigation():
    response = client.post(
        "/breach-check",
        json={"email": "alex.chen@example.com", "password": "winter2024!"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["risk"]["rating"] == "critical"
    assert payload["password_summary"]["exposed"] is True
    assert payload["mitigation_suggestions"]


def test_dashboard_returns_latest_alerts_after_check():
    client.post("/breach-check", json={"email": "maria.patel@example.com", "password": "hello@123"})
    response = client.get("/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["compromised_accounts"] >= 1
    assert payload["latest_alerts"]

