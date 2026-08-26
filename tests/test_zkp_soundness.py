"""Attestation integrity tests.

The scheme is a keyed hash commitment, not a zk-SNARK — but it must at minimum
bind a proof to its statement and reject tampering. These tests exist because
an earlier version accepted arbitrary bytes as a valid proof.
"""

from __future__ import annotations

import pytest

from src.blue_team.zkp_verification import ZKPFraudSystem

FEATURES = [10, 20, 30, 40, 50]
WEIGHTS = [10, 15, 20, 25, 30]


@pytest.fixture()
def system():
    return ZKPFraudSystem(threshold=128)


def test_valid_proof_verifies(system):
    proof = system.prove_fraud_check(FEATURES, WEIGHTS)
    result = system.verify_fraud_check(proof, FEATURES, proof["model_hash"])
    assert result["proof_valid"] is True


def test_garbage_proof_is_rejected(system):
    """Arbitrary bytes must not verify."""
    junk = {"a": "00", "b": "00", "c": "00", "public_signals": []}
    assert system.verifier.verify(junk, FEATURES) is False


def test_tampered_proof_is_rejected(system):
    proof = system.prove_fraud_check(FEATURES, WEIGHTS)
    tampered = dict(proof)
    tampered["c"] = ("0" * len(proof["c"]))
    assert system.verifier.verify(tampered, FEATURES + [proof["model_hash"]]) is False


def test_proof_is_bound_to_its_statement(system):
    """A proof for one statement must not verify against a different one."""
    proof = system.prove_fraud_check(FEATURES, WEIGHTS)
    other_features = [99, 98, 97, 96, 95]
    assert system.verifier.verify(proof, other_features + [proof["model_hash"]]) is False


def test_tampered_public_signals_are_rejected(system):
    """Flipping the fraud verdict must invalidate the attestation."""
    proof = system.prove_fraud_check(FEATURES, WEIGHTS)
    tampered = dict(proof)
    signals = list(proof.get("public_signals", []))
    if not signals:
        pytest.skip("circuit produced no public signals")
    signals[0] = 1 - signals[0] if signals[0] in (0, 1) else signals[0] + 1
    tampered["public_signals"] = signals
    assert system.verifier.verify(tampered, FEATURES + [proof["model_hash"]]) is False


def test_missing_fields_do_not_raise(system):
    assert system.verifier.verify({}, FEATURES) is False
    assert system.verifier.verify({"a": "zz", "b": "zz", "c": "zz"}, FEATURES) is False


def test_certificate_does_not_claim_zk_snark(system):
    """The certificate must not overstate what the scheme provides."""
    cert = system.generate_verification_certificate()
    assert cert["is_zk_snark"] is False
    assert "groth16-simulated" not in cert["proof_type"]
    assert "disclaimer" in cert


def test_commitment_binds_weights(system):
    """Pedersen commitment must reject a different opening."""
    commitment, rand = system.commitment_scheme.commit(12345)
    assert system.commitment_scheme.verify(commitment, 12345, rand) is True
    assert system.commitment_scheme.verify(commitment, 54321, rand) is False
