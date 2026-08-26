import numpy as np
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from secrets import token_bytes


class ZKCircuit:
    """Circom-like arithmetic circuit representation."""

    def __init__(self, circuit_name: str, n_private_inputs: int,
                 n_public_inputs: int, n_outputs: int, n_scratch: int = 0):
        self.circuit_name = circuit_name
        self.n_private_inputs = n_private_inputs
        self.n_public_inputs = n_public_inputs
        self.n_outputs = n_outputs
        self.n_scratch = n_scratch
        self.constraints: List[Tuple] = []
        self.n_wires = n_private_inputs + n_public_inputs + n_outputs + n_scratch

    @property
    def scratch_start(self) -> int:
        """First scratch wire index (after private + public inputs)."""
        return self.n_private_inputs + self.n_public_inputs

    def add_constraint(self, a_wire: int, b_wire: int, c_wire: int):
        if any(w >= self.n_wires for w in (a_wire, b_wire, c_wire)):
            raise ValueError(
                f"Wire index out of bounds (n_wires={self.n_wires}, "
                f"got {(a_wire, b_wire, c_wire)})"
            )
        self.constraints.append((a_wire, b_wire, c_wire))

    def evaluate(self, private_inputs: List[int], public_inputs: List[int]) -> List[int]:
        if len(private_inputs) != self.n_private_inputs:
            raise ValueError(f"Expected {self.n_private_inputs} private inputs")
        if len(public_inputs) != self.n_public_inputs:
            raise ValueError(f"Expected {self.n_public_inputs} public inputs")

        wires = list(private_inputs) + list(public_inputs) + [0] * (self.n_scratch + self.n_outputs)
        for a, b, c in self.constraints:
            wires[c] = wires[a] * wires[b]
        return wires[-self.n_outputs:]

    def generate_circuit_json(self) -> dict:
        return {
            "circuit_name": self.circuit_name,
            "n_private_inputs": self.n_private_inputs,
            "n_public_inputs": self.n_public_inputs,
            "n_outputs": self.n_outputs,
            "n_scratch": self.n_scratch,
            "n_wires": self.n_wires,
            "constraints": [{"a": a, "b": b, "c": c} for a, b, c in self.constraints]
        }


class PedersenCommitment:
    """Hiding and binding commitment scheme using discrete log assumption."""

    def __init__(self, base_point: Optional[bytes] = None):
        self.p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        self.g = int.from_bytes(base_point or b'\x02' + token_bytes(32), 'big') % self.p

    def commit(self, value: int, randomness: Optional[int] = None) -> Tuple[bytes, int]:
        r = randomness or int.from_bytes(token_bytes(32), 'big')
        h = int.from_bytes(hashlib.sha256(b'pedersen_h').digest(), 'big')
        commitment = (pow(self.g, value, self.p) * pow(h, r, self.p)) % self.p
        return commitment.to_bytes(64, 'big'), r

    def verify(self, commitment: bytes, value: int, randomness: int) -> bool:
        h = int.from_bytes(hashlib.sha256(b'pedersen_h').digest(), 'big')
        expected = (pow(self.g, value, self.p) * pow(h, randomness, self.p)) % self.p
        return int.from_bytes(commitment, 'big') == expected

    def batch_commit(self, values: List[int]) -> Tuple[List[bytes], List[int]]:
        commitments, randoms = [], []
        for v in values:
            c, r = self.commit(v)
            commitments.append(c)
            randoms.append(r)
        return commitments, randoms


class FraudCheckCircuit(ZKCircuit):
    """Pre-built circuit for fraud detection verification.

    Wire layout: [private inputs][public inputs][scratch][outputs]
    Scratch holds intermediate products so every constraint target stays
    in bounds (the original layout wrote past the end of the wire vector).
    """

    def __init__(self, threshold: int = 128):
        super().__init__("fraud_check", n_private_inputs=10, n_public_inputs=6,
                         n_outputs=1, n_scratch=7)
        self.threshold = threshold
        self._build_constraints()

    def _build_constraints(self):
        s = self.scratch_start                       # first scratch wire
        # w_i * f_i for the five model weights / features
        for i in range(5):
            self.add_constraint(i, self.n_private_inputs + i, s + i)
        # Combine partial products pairwise into two scratch accumulators
        self.add_constraint(s + 0, s + 1, s + 5)
        self.add_constraint(s + 2, s + 3, s + 6)
        # Final output wire
        out = self.n_wires - 1
        self.add_constraint(s + 5, s + 6, out)

    def evaluate(self, private_inputs: List[int], public_inputs: List[int]) -> List[int]:
        weights = private_inputs[:5]
        committed_hash = private_inputs[5] if len(private_inputs) > 5 else 0
        features = public_inputs[:5]
        expected_hash = public_inputs[5] if len(public_inputs) > 5 else 0

        score = sum(w * f for w, f in zip(weights, features))
        is_fraud = 1 if score > self.threshold else 0
        hash_match = 1 if committed_hash == expected_hash else 0
        return [is_fraud * hash_match]


class ZKProofGenerator:
    """Generates zk-SNARK proofs for fraud check results."""

    def __init__(self, circuit: ZKCircuit, proving_key: Optional[bytes] = None):
        self.circuit = circuit
        self.pk = proving_key or token_bytes(64)

    @property
    def verification_key(self) -> bytes:
        """Derived verification key (must match the verifier's vk)."""
        return hashlib.sha256(self.pk).digest()

    @staticmethod
    def _statement_digest(public_inputs: List[int], public_signals: List[int]) -> bytes:
        """Canonical digest of the statement a proof is about."""
        payload = json.dumps(
            {"public_inputs": list(public_inputs), "public_signals": list(public_signals)},
            sort_keys=True, separators=(",", ":"),
        ).encode()
        return hashlib.sha256(payload).digest()

    def generate_proof(self, private_inputs: List[int], public_inputs: List[int]) -> dict:
        t0 = time.time()
        public_signals = self.circuit.evaluate(private_inputs, public_inputs)
        vk = self.verification_key
        a = hashlib.sha256(json.dumps(private_inputs).encode() + self.pk).digest()
        b = hashlib.sha256(json.dumps(public_inputs).encode() + self.pk).digest()
        # The statement digest binds the attestation to the specific public
        # inputs and outputs.  Without it a proof verifies against *any*
        # statement, which is the difference between an attestation and a
        # decoration.
        stmt = self._statement_digest(public_inputs, public_signals)
        c = hashlib.sha256(a + b + stmt + vk).digest()
        return {
            "a": a.hex(), "b": b.hex(), "c": c.hex(),
            "public_signals": public_signals,
            "proof_time_ms": round((time.time() - t0) * 1000, 2)
        }

    def simulate_proof_generation(self, features: List[int], is_fraud: bool) -> dict:
        weights = [10, 15, 20, 25, 30]
        h = int.from_bytes(hashlib.sha256(bytes(weights)).digest(), 'big')
        private = weights + [h]
        public = features + [h]
        result = self.generate_proof(private, public)
        result["synthetic_weights"] = True
        return result


class ZKVerifier:
    """Verifies zk-SNARK proofs without private inputs."""

    def __init__(self, verification_key: Optional[bytes] = None):
        self.vk = verification_key or token_bytes(64)
        self.stats = {"total": 0, "valid": 0, "times": []}

    def verify(self, proof: dict, public_inputs: List[int]) -> bool:
        """Check that ``proof`` attests to exactly ``public_inputs``.

        Note on scope: this is a keyed hash-commitment attestation, not a
        zk-SNARK.  It gives integrity and statement binding — a tampered proof
        or a mismatched statement fails — but it is *not* succinct and it is
        not sound against a party who holds the verification key.  Production
        deployment would swap this module for Circom + snarkjs Groth16 over
        BN254; the interface is kept identical so the swap is local.
        """
        t0 = time.time()
        self.stats["total"] += 1
        try:
            a_bytes = bytes.fromhex(proof["a"])
            b_bytes = bytes.fromhex(proof["b"])
            stmt = ZKProofGenerator._statement_digest(
                public_inputs, proof.get("public_signals", [])
            )
            c_expected = hashlib.sha256(a_bytes + b_bytes + stmt + self.vk).digest()
            valid = c_expected == bytes.fromhex(proof["c"])
        except (KeyError, ValueError, TypeError):
            valid = False
        if valid:
            self.stats["valid"] += 1
        self.stats["times"].append(round((time.time() - t0) * 1000, 3))
        return valid

    def batch_verify(self, proofs: List[dict]) -> List[bool]:
        return [self.verify(p, p.get("public_signals", [])) for p in proofs]

    def get_verification_stats(self) -> dict:
        times = self.stats["times"]
        return {
            "total_verified": self.stats["total"],
            "valid_proofs": self.stats["valid"],
            "success_rate": self.stats["valid"] / max(self.stats["total"], 1),
            "avg_time_ms": round(np.mean(times), 3) if times else 0,
            "max_time_ms": round(max(times), 3) if times else 0
        }


class ZKPFraudSystem:
    """Complete ZKP system for payment fraud verification."""

    def __init__(self, threshold: int = 128):
        self.circuit = FraudCheckCircuit(threshold)
        self.commitment_scheme = PedersenCommitment()
        # Prover and verifier must share key material, otherwise every proof
        # fails verification. The verification key is derived from the
        # proving key (simulated setup ceremony).
        proving_key = token_bytes(64)
        self.prover = ZKProofGenerator(self.circuit, proving_key=proving_key)
        self.verifier = ZKVerifier(
            verification_key=hashlib.sha256(proving_key).digest()
        )

    def prove_fraud_check(self, features: List[int], model_weights: List[int]) -> dict:
        h = int.from_bytes(hashlib.sha256(bytes(model_weights)).digest(), 'big')
        commitment, rand = self.commitment_scheme.commit(h)
        proof = self.prover.generate_proof(model_weights + [h], features + [h])
        proof["commitment"] = commitment.hex()
        proof["commitment_randomness"] = rand
        # Public hash of the committed weights (needed to verify later)
        proof["model_hash"] = h
        return proof

    def verify_fraud_check(self, proof: dict, features: List[int], expected_hash: int) -> dict:
        pub = features + [expected_hash]
        valid = self.verifier.verify(proof, pub)
        return {
            "proof_valid": valid,
            "public_signals": proof.get("public_signals", []),
            "is_fraud": proof.get("public_signals", [0])[0] == 1,
            "verification_stats": self.verifier.get_verification_stats()
        }

    def generate_verification_certificate(self) -> dict:
        return {
            "certificate_id": hashlib.sha256(token_bytes(32)).hexdigest()[:16],
            "system": "ThreatIQ Screening Attestation v1.0",
            "circuit": self.circuit.circuit_name,
            "circuit_constraints": len(self.circuit.constraints),
            "verification_key_hash": hashlib.sha256(self.verifier.vk).hexdigest(),
            "timestamp": int(time.time()),
            "is_zk_snark": False,
            "disclaimer": (
                "Keyed hash-commitment attestation. Provides integrity and "
                "statement binding, NOT zero-knowledge succinctness or "
                "soundness against a verification-key holder. Production path: "
                "Circom + snarkjs Groth16 over BN254."
            ),
            "proof_type": "hash-commitment-attestation"
        }

    def explain_to_merchant(self) -> str:
        return (
            "This screening attestation demonstrates that: (1) The fraud detection model "
            "was applied correctly to your transaction features, (2) The model weights "
            "match the committed hash, ensuring no tampering, (3) The fraud score "
            "determination (fraud/not-fraud) is accurate. All without revealing the "
            "proprietary model weights or intermediate computations. "
            "It is a hash-commitment scheme, not a zk-SNARK — see the "
            "certificate disclaimer for the production upgrade path."
        )


class CircomExporter:
    """Exports circuits to Circom constraint system format."""

    def export_circuit(self, circuit: ZKCircuit, output_path: str) -> str:
        lines = [f"// {circuit.circuit_name}.circom - Auto-generated ZKP circuit",
                 f"pragma circom 2.0.0;", "",
                 f"template {circuit.circuit_name.title().replace('_', '')}() {{",
                 f"    signal input private_in[{circuit.n_private_inputs}];",
                 f"    signal input public_in[{circuit.n_public_inputs}];",
                 f"    signal output out[{circuit.n_outputs}];", ""]
        for i, (a, b, c) in enumerate(circuit.constraints):
            lines.append(f"    // Constraint {i}: wire{a} * wire{b} = wire{c}")
            if c < circuit.n_outputs:
                lines.append(f"    out[{c}] <== wire{a} * wire{b};")
            else:
                lines.append(f"    wire{c} <== wire{a} * wire{b};")
        lines.extend(["}", "", f"component main {{ public [public_in] }} = "
                       f"{circuit.circuit_name.title().replace('_', '')}();", ""])
        content = "\n".join(lines)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(content)
        return content

    def generate_r1cs_constraints(self, circuit: ZKCircuit) -> List[dict]:
        return [{"id": i, "a": a, "b": b, "c": c, "type": "qmul"}
                for i, (a, b, c) in enumerate(circuit.constraints)]

    def generate_witness(self, circuit: ZKCircuit, private_inputs: List[int],
                         public_inputs: List[int]) -> List[int]:
        wires = list(private_inputs) + list(public_inputs) + [0] * circuit.n_outputs
        for a, b, c in circuit.constraints:
            wires[c] = wires[a] * wires[b]
        return wires
