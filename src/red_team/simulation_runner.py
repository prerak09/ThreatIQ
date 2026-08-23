"""
Simulation Runner
Orchestrates the red team vs blue team simulation loop
"""

import time
import json
import random
import threading
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from collections import deque
from pathlib import Path

if TYPE_CHECKING:
    from ..blue_team.active_learning_loop import ActiveLearningLoop

try:
    from ..threat_intel.generator import ThreatIntelGenerator
    from .agents import AttackerAgent, VictimAgent, MerchantEngine, Transaction
    from .ISO20022_formatter import ISO20022Formatter
except ImportError:
    from threat_intel.generator import ThreatIntelGenerator
    from red_team.agents import AttackerAgent, VictimAgent, MerchantEngine, Transaction
    from red_team.ISO20022_formatter import ISO20022Formatter


# ---------------------------------------------------------------------------
# Canonical ML feature schema — single source of truth shared by training,
# serving and active learning so dimensions can never drift apart again.
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    "amount", "hour", "day_of_week", "geo_lat", "geo_long",
    "behavioral_score", "auth_channel_encoded", "mcc_encoded",
    "is_card_present", "amount_log",
]

_AUTH_CHANNEL_ENCODING = {
    "card_present": 0.0,
    "card_not_present": 1.0,
    "tokenized": 2.0,
    "biometric": 3.0,
    "voice_biometric": 4.0,
    "pin": 5.0,
    "otp": 6.0,
}


def extract_features(transaction: Transaction) -> Dict[str, float]:
    """Extract the canonical ML feature dict from a transaction."""
    ts = datetime.fromisoformat(transaction.timestamp)
    return {
        "amount": float(transaction.amount),
        "hour": float(ts.hour),
        "day_of_week": float(ts.weekday()),
        "geo_lat": float(transaction.geo_lat),
        "geo_long": float(transaction.geo_long),
        "behavioral_score": float(transaction.behavioral_biometrics_score),
        # Deterministic encoding (hash() is randomised per process)
        "auth_channel_encoded": _AUTH_CHANNEL_ENCODING.get(transaction.auth_channel, 0.0),
        "mcc_encoded": float(int(transaction.merchant_category_code)),
        "is_card_present": 1.0 if transaction.auth_channel == "card_present" else 0.0,
        "amount_log": float(np.log1p(transaction.amount)),
    }


class SimulationRunner:
    """
    Main simulation orchestrator for the Adversarial Arena
    
    Coordinates:
    - Red Team: Attack generation and injection
    - Blue Team: Detection and response
    - Merchant: Transaction processing
    - Analytics: Metrics and reporting
    """

    def __init__(
        self,
        num_victims: int = 500,
        fraud_ratio: float = 0.15,
        transaction_rate_tps: float = 10.0,
        enable_active_learning: bool = True
    ):
        """
        Initialize simulation runner
        
        Args:
            num_victims: Number of simulated victim users
            fraud_ratio: Ratio of fraudulent transactions (0-1)
            transaction_rate_tps: Transactions per second
            enable_active_learning: Enable blue team active learning
        """
        self.fraud_ratio = fraud_ratio
        self.transaction_rate_tps = transaction_rate_tps
        self.enable_active_learning = enable_active_learning
        
        # Initialize components
        print("[INIT] Initializing Threat Intelligence Generator...")
        self.threat_gen = ThreatIntelGenerator(seed=42)
        
        print("[INIT] Generating attack vectors...")
        self.threat_gen.generate_batch(count=20)
        
        print("[INIT] Initializing Agent Systems...")
        self.attacker = AttackerAgent(
            attack_vectors=self.threat_gen.taxonomy.vectors,
            proxy_pool_size=200
        )
        self.victim = VictimAgent(num_users=num_victims)
        self.merchant = MerchantEngine(
            merchant_id="MERCH-ARENA-001",
            fraud_detection_enabled=True,
            processing_latency_ms=15.0
        )
        
        # ISO 20022 Formatter
        self.formatter = ISO20022Formatter()
        
        # Simulation state
        self.is_running = False
        self.transaction_buffer = deque(maxlen=10000)
        self.metrics_history = deque(maxlen=1000)
        self._lock = threading.Lock()
        
        # Callbacks for real-time updates
        self.on_transaction_generated: Optional[Callable] = None
        self.on_transaction_processed: Optional[Callable] = None
        self.on_metrics_updated: Optional[Callable] = None
        self.on_fraud_detected: Optional[Callable] = None
        
        # Blue team callback (injected by API)
        self.blue_team_classifier: Optional[Callable] = None

        # Active learning loop (optional — wired by the API layer)
        self.active_learning: Optional["ActiveLearningLoop"] = None
        self._al_batch_window: List[Dict] = []
        self._al_eval_every: int = 50  # evaluate every N transactions

        # Statistics
        self.stats = {
            "start_time": None,
            "total_transactions": 0,
            "fraud_injected": 0,
            "fraud_detected": 0,
            "fraud_missed": 0,
            "false_positives": 0,
            "legitimate_total": 0,
            "processing_times": []
        }

    def set_blue_team_classifier(self, classifier_fn: Callable) -> None:
        """Set the blue team classification function"""
        self.blue_team_classifier = classifier_fn

    def _generate_batch(self, batch_size: int = 10) -> List[Transaction]:
        """Generate a batch of mixed legitimate and fraudulent transactions"""
        transactions = []
        
        for _ in range(batch_size):
            # Decide if this transaction is fraudulent
            is_fraud = random.random() < self.fraud_ratio
            
            if is_fraud:
                tx = self.attacker.generate_transaction()
                self.stats["fraud_injected"] += 1
            else:
                tx = self.victim.generate_transaction()
                self.stats["legitimate_total"] += 1
            
            # Format as ISO 20022
            iso_message = self.formatter.format_credit_transfer(tx)
            tx.iso20022_payload = json.dumps(iso_message)
            
            transactions.append(tx)
            self.stats["total_transactions"] += 1
        
        return transactions

    def _process_transaction(self, transaction: Transaction) -> Dict:
        """Process a transaction through the merchant and blue team"""
        start_time = time.time()

        # Blue team classification (if available)
        blue_team_result = None
        features: Optional[Dict[str, float]] = None
        if self.blue_team_classifier:
            try:
                features = extract_features(transaction)
                blue_team_result = self.blue_team_classifier(features)
            except Exception as e:
                blue_team_result = {"error": str(e), "is_fraud": False, "confidence": 0.0}

        # Merchant processing
        merchant_result = self.merchant.process_transaction(transaction)

        # Update detection metrics (confusion-matrix bookkeeping)
        if blue_team_result is not None:
            predicted_fraud = bool(blue_team_result.get("is_fraud", False))
            if transaction.is_fraud:
                if predicted_fraud:
                    self.stats["fraud_detected"] += 1
                else:
                    self.stats["fraud_missed"] += 1
            elif predicted_fraud:
                self.stats["false_positives"] += 1

        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        self.stats["processing_times"].append(processing_time)

        # Keep only last 1000 processing times
        if len(self.stats["processing_times"]) > 1000:
            self.stats["processing_times"] = self.stats["processing_times"][-1000:]

        result = {
            "type": "attack" if transaction.is_fraud else "transaction",
            "id": transaction.transaction_id,
            "transaction_id": transaction.transaction_id,
            "timestamp": transaction.timestamp,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "channel": transaction.auth_channel,
            "auth_channel": transaction.auth_channel,
            "card_last4": transaction.card_number_last4,
            "ip_address": transaction.ip_address,
            "device_fingerprint": transaction.device_fingerprint,
            "merchant_category_code": transaction.merchant_category_code,
            "geo_lat": transaction.geo_lat,
            "geo_long": transaction.geo_long,
            "is_fraud": transaction.is_fraud,
            "attack_vector": transaction.attack_vector_id,
            "attack_vector_id": transaction.attack_vector_id,
            "merchant_result": merchant_result,
            "blue_team_result": blue_team_result,
            "features": features,
            "blue_team_confidence": float(blue_team_result.get("confidence", 0.0)) if blue_team_result else None,
            "blue_team_flagged": bool(blue_team_result.get("is_fraud", False)) if blue_team_result else False,
            "status": (
                "detected" if (blue_team_result and blue_team_result.get("is_fraud"))
                else "missed" if transaction.is_fraud
                else "approved"
            ),
            "processing_time_ms": round(processing_time, 2),
            "iso20022_payload": transaction.iso20022_payload
        }

        return result

    def _feed_active_learning(self, result: Dict) -> None:
        """Buffer a processed result and periodically evaluate + retrain."""
        if not self.active_learning or result.get("blue_team_result") is None:
            return
        self._al_batch_window.append(result)
        if len(self._al_batch_window) < self._al_eval_every:
            return

        window = self._al_batch_window
        self._al_batch_window = []
        y_true = [1 if r["is_fraud"] else 0 for r in window]
        y_pred = [1 if r["blue_team_flagged"] else 0 for r in window]
        y_proba = [r["blue_team_confidence"] or 0.0 for r in window]
        timestamps = [time.time()] * len(window)
        try:
            self.active_learning.evaluate_batch(
                np.array(y_true), np.array(y_pred), np.array(y_proba),
                transactions=window, timestamps=timestamps,
            )
            self.active_learning.trigger_retrain()
        except Exception as e:
            print(f"[AL] active-learning evaluation error: {e}")

    def _simulation_loop(self) -> None:
        """Main simulation loop"""
        interval = 1.0 / self.transaction_rate_tps
        
        while self.is_running:
            batch_start = time.time()
            
            # Generate transactions
            batch_size = max(1, int(self.transaction_rate_tps / 10))
            transactions = self._generate_batch(batch_size)
            
            # Process each transaction
            for tx in transactions:
                if not self.is_running:
                    break

                result = self._process_transaction(tx)

                with self._lock:
                    self.transaction_buffer.append(result)

                # Notify callbacks
                if self.on_transaction_generated:
                    self.on_transaction_generated(result)

                if result.get("is_fraud") and self.on_fraud_detected:
                    self.on_fraud_detected(result)

                if self.on_transaction_processed:
                    self.on_transaction_processed(result)

                # Closed-loop active learning
                self._feed_active_learning(result)
            
            # Update metrics
            self._update_metrics()
            
            # Maintain transaction rate
            elapsed = time.time() - batch_start
            sleep_time = max(0, interval * batch_size - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_metrics(self) -> None:
        """Update simulation metrics"""
        with self._lock:
            total = self.stats["total_transactions"]
            fraud_injected = self.stats["fraud_injected"]
            fraud_detected = self.stats["fraud_detected"]
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "total_transactions": total,
                "transactions_per_second": self.transaction_rate_tps,
                "fraud_injected": fraud_injected,
                "fraud_detected": fraud_detected,
                "fraud_missed": self.stats["fraud_missed"],
                "detection_rate": round(
                    fraud_detected / max(fraud_injected, 1) * 100, 2
                ),
                "false_negative_rate": round(
                    self.stats["fraud_missed"] / max(fraud_injected, 1) * 100, 2
                ),
                "precision": round(
                    fraud_detected / max(fraud_detected + self.stats.get("false_positives", 0), 1) * 100, 2
                ),
                "avg_latency_ms": round(
                    sum(self.stats["processing_times"]) / max(len(self.stats["processing_times"]), 1), 2
                ),
                "merchant_stats": self.merchant.get_statistics(),
                "threat_stats": self.threat_gen.get_statistics()
            }
            
            self.metrics_history.append(metrics)
            
            if self.on_metrics_updated:
                self.on_metrics_updated(metrics)

    def start(self) -> None:
        """Start the simulation"""
        if self.is_running:
            print("[WARN] Simulation already running")
            return
        
        self.is_running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        print(f"[START] Adversarial Arena Simulation Started")
        print(f"[CONFIG] Fraud Ratio: {self.fraud_ratio*100}%")
        print(f"[CONFIG] Transaction Rate: {self.transaction_rate_tps} TPS")
        
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the simulation"""
        self.is_running = False
        print("[STOP] Simulation Stopped")
        
        # Final metrics
        self._update_metrics()

    def inject_custom_attack(
        self,
        attack_type: str,
        count: int = 10
    ) -> List[Dict]:
        """
        Inject a custom attack scenario

        Args:
            attack_type: Attack category value, enum name, vector id, or
                friendly name (e.g. "multi_hop_cnp", "MULTI_HOP_CNP",
                "ATK-002", "Multi-Hop CNP")
            count: Number of attack transactions

        Returns:
            List of injected attack results
        """
        matching_vectors = self._resolve_attack_vectors(attack_type)
        if not matching_vectors:
            raise ValueError(
                f"Unknown attack_type '{attack_type}'. "
                f"Valid categories: {sorted(self._all_category_values())}"
            )

        print(f"[INJECT] Injecting {count} {attack_type} attacks")

        # Use a dedicated attacker so the background loop's agent is never
        # mutated mid-flight (race condition).
        injector = AttackerAgent(
            attack_vectors=matching_vectors,
            proxy_pool_size=self.attacker.proxy_pool_size,
            fraud_amount_range=self.attacker.fraud_amount_range,
        )

        results = []
        for _ in range(count):
            tx = injector.generate_transaction()
            iso_message = self.formatter.format_credit_transfer(tx)
            tx.iso20022_payload = json.dumps(iso_message)
            result = self._process_transaction(tx)
            with self._lock:
                self.transaction_buffer.append(result)
            self.stats["fraud_injected"] += 1
            self.stats["total_transactions"] += 1
            results.append(result)

        return results

    def _all_category_values(self) -> List[str]:
        return sorted({v.category.value for v in self.threat_gen.taxonomy.vectors})

    def _resolve_attack_vectors(self, attack_type: str):
        """Match an attack type against vectors by value / name / id."""
        needle = attack_type.strip().lower().replace("-", "_").replace(" ", "_")
        vectors = self.threat_gen.taxonomy.vectors
        # exact matches first (category value, enum name, vector id)
        for key in (
            lambda v: v.category.value.lower(),
            lambda v: v.category.name.lower(),
            lambda v: v.vector_id.lower(),
        ):
            hits = [v for v in vectors if key(v) == needle]
            if hits:
                return hits
        # substring match on category value or friendly name
        hits = [
            v for v in vectors
            if needle in v.category.value.lower()
            or needle in v.category.name.lower()
            or needle in v.name.lower()
        ]
        return hits

    def get_current_metrics(self) -> Dict:
        """Get current simulation metrics"""
        with self._lock:
            if self.metrics_history:
                return self.metrics_history[-1]
            return {}

    def get_transaction_history(
        self,
        limit: int = 100,
        fraud_only: bool = False
    ) -> List[Dict]:
        """Get recent transaction history"""
        history = self.snapshot_transactions()
        if fraud_only:
            history = [t for t in history if t.get("is_fraud")]
        return history[-limit:]

    def snapshot_transactions(self, limit: Optional[int] = None) -> List[Dict]:
        """Thread-safe copy of the transaction buffer (oldest first)."""
        with self._lock:
            history = list(self.transaction_buffer)
        if limit is not None:
            history = history[-limit:]
        return history

    def get_feature_schema(self) -> Dict[str, Any]:
        """Canonical feature schema used for training and serving."""
        return {"feature_names": list(FEATURE_NAMES), "n_features": len(FEATURE_NAMES)}

    def export_simulation_data(self, output_path: str) -> None:
        """Export all simulation data to JSON"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "simulation_stats": self.stats,
                "threat_taxonomy": self.threat_gen.taxonomy.to_json()
            },
            "transactions": list(self.transaction_buffer),
            "metrics_history": list(self.metrics_history)
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[EXPORT] Simulation data exported to {output_path}")

    def reset(self) -> None:
        """Reset simulation state"""
        self.stop()
        self.transaction_buffer.clear()
        self.metrics_history.clear()
        self.stats = {
            "start_time": None,
            "total_transactions": 0,
            "fraud_injected": 0,
            "fraud_detected": 0,
            "fraud_missed": 0,
            "false_positives": 0,
            "legitimate_total": 0,
            "processing_times": []
        }
        self._al_batch_window = []
        self.merchant = MerchantEngine(
            merchant_id="MERCH-ARENA-001",
            fraud_detection_enabled=True,
            processing_latency_ms=15.0
        )
        print("[RESET] Simulation reset complete")
