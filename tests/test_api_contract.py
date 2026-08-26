"""API contract and abuse-resistance tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import MAX_TRAIN_SAMPLES, app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_reports_all_components(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["components"]["model"] is True
    assert body["components"]["simulation"] is True


def test_train_rejects_oversized_request(client):
    """An unbounded n_samples is a single-request denial of service."""
    r = client.post("/api/model/train", json={"n_samples": MAX_TRAIN_SAMPLES * 100})
    assert r.status_code == 422, "oversized training request was not rejected"


def test_train_accepts_bounded_request(client):
    r = client.post("/api/model/train", json={"n_samples": 200})
    assert r.status_code == 200
    assert "metrics" in r.json()


def test_threshold_bounds_enforced(client):
    assert client.post("/api/model/threshold", json={"threshold": 1.0}).status_code == 422
    assert client.post("/api/model/threshold", json={"threshold": 0.0}).status_code == 422
    assert client.post("/api/model/threshold", json={"threshold": 0.7}).status_code == 200


def test_unknown_attack_type_is_rejected(client):
    r = client.post("/api/attack/inject", json={"attack_type": "../../etc/passwd", "count": 2})
    assert r.status_code == 400
    assert "Unknown attack_type" in r.json()["detail"]


def test_inject_count_is_bounded(client):
    r = client.post("/api/attack/inject", json={"attack_type": "synthetic_identity", "count": 100000})
    assert r.status_code == 422


def test_zkp_verify_rejects_a_forged_proof(client):
    """The endpoint must check the submitted proof, not mint a fresh one."""
    r = client.post("/api/zkp/verify", json={
        "a": "00", "b": "00", "c": "00",
        "public_signals": [1], "public_inputs": [1, 2, 3],
    })
    assert r.status_code == 200
    assert r.json()["valid"] is False, "a forged proof verified successfully"


def test_zkp_verify_accepts_an_issued_proof(client):
    issued = client.post("/api/zkp/prove").json()
    r = client.post(f"/api/zkp/verify?proof_id={issued['proof_id']}")
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_zkp_verify_unknown_id_is_404(client):
    r = client.post("/api/zkp/verify?proof_id=does-not-exist")
    assert r.status_code == 404


def test_zkp_certificate_does_not_claim_zk_snark(client):
    cert = client.get("/api/zkp/certificate").json()
    assert cert["is_zk_snark"] is False


def test_marl_agents_expose_real_history(client):
    body = client.get("/api/marl/agents").json()
    assert "has_data" in body
    for agent in body["agents"]:
        assert "history" in agent
        assert "policy_actions" in agent
        assert abs(sum(agent["policy_actions"].values()) - 1.0) < 1e-2


def test_marl_evolve_produces_measured_values(client):
    r = client.post("/api/marl/evolve?epochs=2")
    assert r.status_code == 200
    body = r.json()
    assert body["evolved"] is True
    assert body["per_agent_evasion"]
    for v in body["per_agent_evasion"].values():
        assert 0.0 <= v <= 1.0


def test_marl_evolve_epochs_are_bounded(client):
    r = client.post("/api/marl/evolve?epochs=100000")
    assert r.status_code == 200
    assert r.json()["epochs_run"] <= 50


def test_xai_explain_missing_transaction_is_404(client):
    r = client.get("/api/xai/explain/definitely-not-a-real-id")
    assert r.status_code == 404


def test_xai_explain_returns_1d_attributions(client):
    """SHAP output must be reduced to one attribution per feature.

    Newer SHAP returns (n_samples, n_features, n_classes) for binary
    classifiers. Passing that through unreduced made every XAI and SAR call
    raise "only integer scalar arrays can be converted to a scalar index".
    """
    client.post("/api/simulation/start", json={
        "num_victims": 100, "fraud_ratio": 0.3, "transaction_rate_tps": 50,
    })
    import time as _t
    _t.sleep(3)
    txs = client.get("/api/transactions?limit=1").json()
    client.post("/api/simulation/stop")
    if not txs:
        pytest.skip("no transactions generated")

    r = client.get(f"/api/xai/explain/{txs[0]['transaction_id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["top_features"], "no attributions returned"
    for name, value in body["top_features"]:
        assert isinstance(name, str)
        assert isinstance(value, float)


def test_sar_generation_succeeds(client):
    r = client.post("/api/sar/generate")
    assert r.status_code == 200
    assert "sar_id" in r.json()
