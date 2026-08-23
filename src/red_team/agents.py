"""
Multi-Agent Simulation Engine
Attacker, Victim, and Merchant agents for payment fraud simulation
"""

import random
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

try:
    from ..threat_intel.taxonomy_schema import AttackVector, AttackCategory
except ImportError:
    from threat_intel.taxonomy_schema import AttackVector, AttackCategory


@dataclass
class Transaction:
    """Standardized transaction record"""
    transaction_id: str
    timestamp: str
    amount: float
    currency: str
    merchant_category_code: str
    card_number_last4: str
    device_fingerprint: str
    ip_address: str
    geo_lat: float
    geo_long: float
    auth_channel: str
    behavioral_biometrics_score: float
    is_fraud: bool
    attack_vector_id: Optional[str] = None
    raw_payload_logs: Dict[str, Any] = field(default_factory=dict)
    iso20022_payload: Optional[str] = None


class AttackerAgent:
    """
    Autonomous attacker agent that generates malicious transaction patterns
    
    Uses threat intelligence to create realistic fraud attempts that test
    payment system defenses with high fidelity.
    """

    def __init__(
        self,
        attack_vectors: List[AttackVector],
        proxy_pool_size: int = 100,
        fraud_amount_range: tuple = (5.0, 500.0)
    ):
        self.attack_vectors = attack_vectors
        self.proxy_pool_size = proxy_pool_size
        self.fraud_amount_range = fraud_amount_range
        self._card_cache: List[Dict] = []
        self._ip_pool: List[str] = self._generate_ip_pool()

    def _generate_ip_pool(self) -> List[str]:
        """Generate realistic IP address pool"""
        return [
            f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            for _ in range(self.proxy_pool_size)
        ]

    def _generate_device_fingerprint(self) -> str:
        """Generate realistic device fingerprint"""
        components = {
            "os": random.choice(["Windows 10", "macOS 14", "iOS 17", "Android 14"]),
            "browser": random.choice(["Chrome 120", "Safari 17", "Firefox 121"]),
            "screen": random.choice(["1920x1080", "2560x1440", "1366x768"]),
            "timezone": random.choice(["America/New_York", "Europe/London", "Asia/Tokyo"]),
            "language": random.choice(["en-US", "en-GB", "fr-FR", "de-DE"])
        }
        raw = "|".join(f"{k}:{v}" for k, v in components.items())
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _generate_card_number(self) -> str:
        """Generate realistic card number (Luhn-valid)"""
        # Use common BIN ranges
        bin_prefixes = ["4111", "5555", "3782", "6011"]
        prefix = random.choice(bin_prefixes)
        
        # Generate remaining digits
        digits = [int(d) for d in prefix]
        while len(digits) < 15:
            digits.append(random.randint(0, 9))
        
        # Calculate Luhn checksum
        total = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 0:
                doubled = digit * 2
                total += doubled if doubled < 10 else doubled - 9
            else:
                total += digit
        check_digit = (10 - (total % 10)) % 10
        digits.append(check_digit)
        
        return "".join(map(str, digits))

    def _select_attack_vector(self) -> AttackVector:
        """Select attack vector based on weighted probability"""
        weights = [v.risk_level.value * v.fidelity_score for v in self.attack_vectors]
        return random.choices(self.attack_vectors, weights=weights, k=1)[0]

    def _generate_fraud_amount(self, vector: AttackVector) -> float:
        """Generate fraud amount based on attack type"""
        if vector.category == AttackCategory.MULTI_HOP_CNP:
            # Micro-transactions for CNP relay
            return round(random.uniform(5.0, 50.0), 2)
        elif vector.category == AttackCategory.SYNTHETIC_IDENTITY:
            # Higher amounts for identity fraud
            return round(random.uniform(100.0, 2000.0), 2)
        elif vector.category == AttackCategory.PROMPT_INJECTION:
            # Variable amounts based on injection success
            return round(random.uniform(50.0, 500.0), 2)
        else:
            return round(random.uniform(*self.fraud_amount_range), 2)

    def _generate_geo_location(self, base_region: str = "US") -> tuple:
        """Generate geographically consistent coordinates"""
        regions = {
            "US": (37.0902, -95.7129, 10.0),
            "EU": (48.8566, 2.3522, 8.0),
            "APAC": (35.6762, 139.6503, 5.0),
            "LATAM": (-15.7975, -47.8919, 7.0)
        }
        lat, long, spread = regions.get(base_region, regions["US"])
        return (
            round(lat + random.gauss(0, spread), 6),
            round(long + random.gauss(0, spread), 6)
        )

    def generate_transaction(
        self, 
        timestamp: Optional[datetime] = None
    ) -> Transaction:
        """
        Generate a single fraudulent transaction
        
        Args:
            timestamp: Optional specific timestamp
        
        Returns:
            Transaction with malicious patterns
        """
        vector = self._select_attack_vector()
        amount = self._generate_fraud_amount(vector)
        geo_lat, geo_long = self._generate_geo_location()
        
        # Behavioral biometrics score (lower = more suspicious)
        bio_score = random.uniform(0.1, 0.4)  # Fraud tends to have lower scores
        
        # Generate auth channel based on attack type
        if vector.category == AttackCategory.VOICE_DEEPFAKE:
            auth_channel = "voice_biometric"
        elif vector.category == AttackCategory.SYNTHETIC_IDENTITY:
            auth_channel = random.choice(["biometric", "pin", "otp"])
        else:
            auth_channel = random.choice(["card_present", "card_not_present", "tokenized"])

        tx_timestamp = timestamp or datetime.now()
        
        transaction = Transaction(
            transaction_id=f"TXN-{hashlib.md5(f'{time.time()}-{random.random()}'.encode()).hexdigest()[:12].upper()}",
            timestamp=tx_timestamp.isoformat(),
            amount=amount,
            currency=random.choice(["USD", "EUR", "GBP", "JPY"]),
            merchant_category_code=random.choice(["5411", "5412", "5812", "5999", "4121"]),
            card_number_last4=self._generate_card_number()[-4:],
            device_fingerprint=self._generate_device_fingerprint(),
            ip_address=random.choice(self._ip_pool),
            geo_lat=geo_lat,
            geo_long=geo_long,
            auth_channel=auth_channel,
            behavioral_biometrics_score=round(bio_score, 4),
            is_fraud=True,
            attack_vector_id=vector.vector_id,
            raw_payload_logs={
                "attack_category": vector.category.value,
                "evasion_technique": random.choice(
                    [s.evasion_technique for s in vector.execution_steps if s.evasion_technique]
                ),
                "fidelity_score": vector.fidelity_score,
                "proxy_rotation": True,
                "session_isolation": True
            }
        )
        
        return transaction


class VictimAgent:
    """
    Generates normal user behavior patterns for baseline comparison
    
    Ensures realistic transaction distributions following:
    - Benford's Law for amounts
    - Time-of-day distributions
    - Geographic consistency
    - Device fingerprint stability
    """

    def __init__(
        self,
        num_users: int = 1000,
        user_base_region: str = "US"
    ):
        self.num_users = num_users
        self.user_base_region = user_base_region
        self._user_profiles = self._generate_user_profiles()

    def _generate_user_profiles(self) -> List[Dict]:
        """Generate realistic user profiles"""
        profiles = []
        for i in range(self.num_users):
            profile = {
                "user_id": f"USR-{i:06d}",
                "home_region": random.choice(["US", "EU", "APAC", "LATAM"]),
                "typical_amount_range": (
                    random.uniform(10.0, 100.0),
                    random.uniform(100.0, 500.0)
                ),
                "preferred_mcc": random.choice(["5411", "5812", "5999", "4121"]),
                "device_count": random.randint(1, 4),
                "typical_hour_distribution": self._generate_hour_distribution(),
                "spending_pattern": random.choice(["conservative", "moderate", "aggressive"])
            }
            profiles.append(profile)
        return profiles

    def _generate_hour_distribution(self) -> List[float]:
        """Generate realistic hourly transaction distribution"""
        # Peak hours: 10am-2pm and 6pm-9pm
        hours = []
        for h in range(24):
            if 10 <= h <= 14:
                weight = 0.8 + random.uniform(0, 0.2)
            elif 18 <= h <= 21:
                weight = 0.7 + random.uniform(0, 0.2)
            elif 2 <= h <= 5:
                weight = 0.05 + random.uniform(0, 0.05)
            else:
                weight = 0.3 + random.uniform(0, 0.3)
            hours.append(weight)
        
        # Normalize
        total = sum(hours)
        return [h / total for h in hours]

    def _generate_benford_amount(self) -> float:
        """Generate amount following Benford's Law"""
        # Benford's distribution for first digit
        benford_probs = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]
        first_digit = np.random.choice(range(1, 10), p=benford_probs)
        
        # Generate remaining digits
        magnitude = random.choice([1, 10, 100, 1000])
        return round(first_digit * magnitude + random.uniform(0, magnitude - 0.01), 2)

    def generate_transaction(
        self, 
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Transaction:
        """
        Generate a legitimate transaction
        
        Args:
            user_id: Optional specific user ID
            timestamp: Optional specific timestamp
        
        Returns:
            Transaction representing normal user behavior
        """
        profile = random.choice(self._user_profiles) if not user_id else \
            next((p for p in self._user_profiles if p["user_id"] == user_id), 
                  random.choice(self._user_profiles))
        
        # Select hour based on distribution
        hour = np.random.choice(24, p=profile["typical_hour_distribution"])
        tx_timestamp = timestamp or datetime.now().replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Generate amount with Benford's Law
        amount = self._generate_benford_amount()
        
        # Keep within user's typical range
        low, high = profile["typical_amount_range"]
        amount = max(low, min(high, amount))
        
        # Generate device fingerprint
        device_fp = hashlib.md5(
            f"{profile['user_id']}-device-{random.randint(0, profile['device_count']-1)}".encode()
        ).hexdigest()[:16]
        
        # Geographic consistency
        regions = {
            "US": (37.0902, -95.7129, 5.0),
            "EU": (48.8566, 2.3522, 4.0),
            "APAC": (35.6762, 139.6503, 3.0),
            "LATAM": (-15.7975, -47.8919, 4.0)
        }
        lat, long, spread = regions.get(profile["home_region"], regions["US"])
        geo_lat = round(lat + random.gauss(0, spread), 6)
        geo_long = round(long + random.gauss(0, spread), 6)
        
        # High behavioral biometrics for legitimate users
        bio_score = random.uniform(0.7, 0.99)
        
        transaction = Transaction(
            transaction_id=f"TXN-{hashlib.md5(f'{time.time()}-{random.random()}'.encode()).hexdigest()[:12].upper()}",
            timestamp=tx_timestamp.isoformat(),
            amount=amount,
            currency=random.choice(["USD", "EUR", "GBP"]),
            merchant_category_code=profile["preferred_mcc"],
            card_number_last4=f"{random.randint(1000, 9999)}",
            device_fingerprint=device_fp,
            ip_address=f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            geo_lat=geo_lat,
            geo_long=geo_long,
            auth_channel=random.choice(["card_present", "card_not_present", "tokenized", "biometric"]),
            behavioral_biometrics_score=round(bio_score, 4),
            is_fraud=False,
            raw_payload_logs={
                "user_id": profile["user_id"],
                "spending_pattern": profile["spending_pattern"],
                "session_duration": random.randint(30, 300)
            }
        )
        
        return transaction


class MerchantEngine:
    """
    Mock e-commerce payment gateway for transaction processing
    
    Simulates real-world merchant behavior including:
    - Transaction validation
    - Response generation
    - Latency simulation
    - Fraud scoring integration
    """

    def __init__(
        self,
        merchant_id: str = "MERCH-001",
        fraud_detection_enabled: bool = True,
        processing_latency_ms: float = 50.0
    ):
        self.merchant_id = merchant_id
        self.fraud_detection_enabled = fraud_detection_enabled
        self.processing_latency_ms = processing_latency_ms
        self._transaction_log: List[Dict] = []
        self._log_lock = threading.Lock()
        self._stats = {
            "total_processed": 0,
            "approved": 0,
            "declined": 0,
            "flagged": 0
        }

    @staticmethod
    def _parse_ts(value: Any) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    def _validate_transaction(self, transaction: Transaction) -> Dict:
        """
        Validate transaction against merchant rules
        
        Returns:
            Validation result with status and reasons
        """
        issues = []
        
        # Amount validation
        if transaction.amount <= 0:
            issues.append("INVALID_AMOUNT")
        elif transaction.amount > 10000:
            issues.append("HIGH_AMOUNT")

        tx_ts = self._parse_ts(transaction.timestamp)
        
        with self._log_lock:
            recent = list(self._transaction_log[-100:])

        if tx_ts is not None:
            cutoff = tx_ts - timedelta(minutes=5)

            # Velocity check (parsed datetime comparison, not ISO strings)
            recent_count = 0
            last_same_card: Optional[Dict] = None
            for t in recent:
                t_ts = self._parse_ts(t.get("timestamp"))
                if (
                    t.get("card_last4") == transaction.card_number_last4
                    and t_ts is not None and t_ts >= cutoff
                ):
                    recent_count += 1
                    if last_same_card is None or (t_ts > (self._parse_ts(last_same_card.get("timestamp")) or t_ts)):
                        last_same_card = t
            if recent_count > 5:
                issues.append("VELOCITY_EXCEEDED")

            # Geo-velocity check against the most recent same-card transaction
            if last_same_card is not None:
                prev_ts = self._parse_ts(last_same_card.get("timestamp"))
                if prev_ts is not None:
                    time_diff = (tx_ts - prev_ts).total_seconds() / 3600
                    dist = self._calculate_distance(
                        last_same_card.get("geo_lat", 0), last_same_card.get("geo_long", 0),
                        transaction.geo_lat, transaction.geo_long
                    )
                    if time_diff > 0 and dist / time_diff > 500:  # 500 km/h threshold
                        issues.append("IMPOSSIBLE_TRAVEL")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def _calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    def process_transaction(self, transaction: Transaction) -> Dict:
        """
        Process a transaction through the merchant gateway
        
        Args:
            transaction: Transaction to process
        
        Returns:
            Processing result with approval status and metadata
        """
        self._stats["total_processed"] += 1
        
        # Simulate processing latency
        time.sleep(self.processing_latency_ms / 1000)
        
        # Validate transaction
        validation = self._validate_transaction(transaction)
        
        # Determine response
        with self._log_lock:
            if not validation["valid"]:
                status = "DECLINED"
                self._stats["declined"] += 1
            elif self.fraud_detection_enabled and transaction.is_fraud:
                # Simulate fraud detection (with some false negatives)
                detection_probability = 0.7 if transaction.behavioral_biometrics_score < 0.5 else 0.4
                if random.random() < detection_probability:
                    status = "FLAGGED"
                    self._stats["flagged"] += 1
                else:
                    status = "APPROVED"
                    self._stats["approved"] += 1
            else:
                status = "APPROVED"
                self._stats["approved"] += 1

            # Log transaction
            self._transaction_log.append({
                "transaction_id": transaction.transaction_id,
                "timestamp": transaction.timestamp,
                "amount": transaction.amount,
                "card_last4": transaction.card_number_last4,
                "geo_lat": transaction.geo_lat,
                "geo_long": transaction.geo_long,
                "status": status,
                "attack_vector_id": transaction.attack_vector_id
            })
        
        return {
            "transaction_id": transaction.transaction_id,
            "status": status,
            "validation": validation,
            "processing_time_ms": self.processing_latency_ms,
            "merchant_id": self.merchant_id,
            "response_code": "00" if status == "APPROVED" else "05" if status == "DECLINED" else "59",
            "authorization_code": f"AUTH-{random.randint(100000, 999999)}" if status == "APPROVED" else None
        }

    def get_statistics(self) -> Dict:
        """Get merchant processing statistics"""
        return {
            **self._stats,
            "approval_rate": round(
                self._stats["approved"] / max(self._stats["total_processed"], 1) * 100, 2
            ),
            "decline_rate": round(
                self._stats["declined"] / max(self._stats["total_processed"], 1) * 100, 2
            ),
            "flag_rate": round(
                self._stats["flagged"] / max(self._stats["total_processed"], 1) * 100, 2
            )
        }
