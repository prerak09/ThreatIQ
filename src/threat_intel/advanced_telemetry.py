"""Advanced payment telemetry schema for transaction analysis and ML feature engineering."""

import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DeviceRenderOptions(Enum):
    """3-D Secure 2.2 device render options."""
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    OOB = "oob"
    HTML_OOB = "html_oob"


class MessageCategory(Enum):
    """3-D Secure 2.2 message category."""
    PA = "pa"
    NPA = "npa"


@dataclass
class ThreeDS2Context:
    """Full 3-D Secure 2.2 authentication context."""
    three_ds_version: str = "2.2.0"
    sdk_app_id: str = ""
    sdk_transaction_id: str = ""
    sdk_ephemeral_public_key: str = ""
    device_render_options: DeviceRenderOptions = DeviceRenderOptions.SINGLE_SELECT
    message_category: MessageCategory = MessageCategory.PA
    three_ds_comp_ind: str = "Y"
    device_channel: str = "app"
    authentication_method: str = "01"
    user_agent: str = ""
    screen_width: int = 1920
    screen_height: int = 1080
    timezone_offset: int = 0
    java_enabled: bool = False
    javascript_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "three_ds_version": self.three_ds_version,
            "sdk_app_id": self.sdk_app_id,
            "sdk_transaction_id": self.sdk_transaction_id,
            "sdk_ephemeral_public_key": self.sdk_ephemeral_public_key,
            "device_render_options": self.device_render_options.value,
            "message_category": self.message_category.value,
            "three_ds_comp_ind": self.three_ds_comp_ind,
            "device_channel": self.device_channel,
            "authentication_method": self.authentication_method,
            "user_agent": self.user_agent,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "timezone_offset": self.timezone_offset,
            "java_enabled": self.java_enabled,
            "javascript_enabled": self.javascript_enabled,
        }


@dataclass
class TLSFingerprint:
    """JA3/JA4 TLS fingerprinting data."""
    ja3_hash: str = ""
    ja3_raw: str = ""
    ja4_hash: str = ""
    ja4_raw: str = ""
    tls_version: str = "TLSv1.3"
    cipher_suite_count: int = 0
    extension_count: int = 0
    has_alpn: bool = True
    supports_http2: bool = True
    signature_algorithm: str = "ecdsa_secp256r1_sha256"

    @classmethod
    def generate_mock(cls) -> "TLSFingerprint":
        """Generate a realistic mock TLS fingerprint."""
        ciphers = [
            "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256", "TLS_AES_128_CCM_SHA256",
        ]
        selected = random.sample(ciphers, k=random.randint(2, 4))
        ja3_raw = (
            f"771,"
            f"{','.join(str(random.randint(0x1301, 0x1305)) for _ in selected)},"
            f"{','.join(str(random.randint(0, 50)) for _ in range(random.randint(5, 15)))}"
        )
        sig_algs = [
            "ecdsa_secp256r1_sha256", "rsa_pss_rsae_sha256",
            "rsa_pkcs1_sha256", "ecdsa_secp384r1_sha384",
        ]
        return cls(
            ja3_hash=uuid.uuid5(uuid.NAMESPACE_URL, ja3_raw).hex,
            ja3_raw=ja3_raw,
            ja4_hash=uuid.uuid4().hex,
            ja4_raw=f"t13d{len(selected):02d}h2_{selected[0].split('_')[1].lower()}",
            tls_version=random.choice(["TLSv1.2", "TLSv1.3"]),
            cipher_suite_count=len(selected),
            extension_count=random.randint(10, 25),
            has_alpn=random.random() > 0.1,
            supports_http2=random.random() > 0.15,
            signature_algorithm=random.choice(sig_algs),
        )


@dataclass
class BrowserFingerprint:
    """Client-side browser fingerprinting data."""
    canvas_hash: str = ""
    webgl_hash: str = ""
    audio_hash: str = ""
    webrtc_ip: str = ""
    platform: str = ""
    language: str = "en-US"
    hardware_concurrency: int = 8
    device_memory: int = 8
    plugins_count: int = 0
    has_adblock: bool = False
    fingerprint_entropy: float = 0.0

    @classmethod
    def generate_mock(cls) -> "BrowserFingerprint":
        """Generate a realistic mock browser fingerprint."""
        platforms = ["Win32", "MacIntel", "Linux x86_64"]
        languages = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES"]
        ip_parts = [str(random.randint(1, 254)) for _ in range(4)]
        return cls(
            canvas_hash=uuid.uuid4().hex[:16],
            webgl_hash=uuid.uuid4().hex[:16],
            audio_hash=uuid.uuid4().hex[:16],
            webrtc_ip=".".join(ip_parts),
            platform=random.choice(platforms),
            language=random.choice(languages),
            hardware_concurrency=random.choice([2, 4, 8, 12, 16]),
            device_memory=random.choice([2, 4, 8, 16]),
            plugins_count=random.randint(2, 8),
            has_adblock=random.random() < 0.25,
            fingerprint_entropy=round(random.uniform(20.0, 80.0), 2),
        )


@dataclass
class BehavioralBiometrics:
    """Mouse, keyboard, touch, and device motion dynamics."""
    mouse_velocity_mean: float = 0.0
    mouse_velocity_std: float = 0.0
    mouse_acceleration_mean: float = 0.0
    mouse_click_interval_mean: float = 0.0
    mouse_path_curvature: float = 0.0
    mouse_idle_ratio: float = 0.0
    keyboard_dwell_mean: float = 0.0
    keyboard_dwell_std: float = 0.0
    keyboard_flight_mean: float = 0.0
    keyboard_flight_std: float = 0.0
    typing_speed_wpm: float = 0.0
    keyboard_error_rate: float = 0.0
    keyboard_backspace_rate: float = 0.0
    touch_pressure_mean: float = 0.0
    touch_area_mean: float = 0.0
    touch_orientation_mean: float = 0.0
    gyroscope_tilt_std: float = 0.0
    accelerometer_magnitude_mean: float = 0.0
    behavioral_consistency_score: float = 0.0
    anomaly_score: float = 0.0

    @classmethod
    def generate_mock(cls, is_fraud: bool = False) -> "BehavioralBiometrics":
        """Generate realistic mock behavioral biometrics.

        Args:
            is_fraud: If True, injects anomalous behavioral patterns.
        """
        if is_fraud:
            return cls(
                mouse_velocity_mean=round(random.uniform(800, 2000), 2),
                mouse_velocity_std=round(random.uniform(200, 600), 2),
                mouse_acceleration_mean=round(random.uniform(5000, 15000), 2),
                mouse_click_interval_mean=round(random.uniform(0.05, 0.3), 4),
                mouse_path_curvature=round(random.uniform(0.1, 0.9), 3),
                mouse_idle_ratio=round(random.uniform(0.01, 0.15), 3),
                keyboard_dwell_mean=round(random.uniform(10, 50), 2),
                keyboard_dwell_std=round(random.uniform(5, 20), 2),
                keyboard_flight_mean=round(random.uniform(20, 100), 2),
                keyboard_flight_std=round(random.uniform(10, 50), 2),
                typing_speed_wpm=round(random.uniform(150, 350), 1),
                keyboard_error_rate=round(random.uniform(0.1, 0.4), 3),
                keyboard_backspace_rate=round(random.uniform(0.15, 0.5), 3),
                touch_pressure_mean=round(random.uniform(0.1, 0.4), 3),
                touch_area_mean=round(random.uniform(10, 50), 1),
                touch_orientation_mean=round(random.uniform(10, 90), 1),
                gyroscope_tilt_std=round(random.uniform(50, 150), 2),
                accelerometer_magnitude_mean=round(random.uniform(15, 30), 2),
                behavioral_consistency_score=round(random.uniform(0.0, 0.4), 3),
                anomaly_score=round(random.uniform(0.6, 1.0), 3),
            )
        return cls(
            mouse_velocity_mean=round(random.uniform(200, 800), 2),
            mouse_velocity_std=round(random.uniform(50, 200), 2),
            mouse_acceleration_mean=round(random.uniform(1000, 5000), 2),
            mouse_click_interval_mean=round(random.uniform(0.3, 1.5), 4),
            mouse_path_curvature=round(random.uniform(0.05, 0.35), 3),
            mouse_idle_ratio=round(random.uniform(0.15, 0.5), 3),
            keyboard_dwell_mean=round(random.uniform(50, 150), 2),
            keyboard_dwell_std=round(random.uniform(15, 60), 2),
            keyboard_flight_mean=round(random.uniform(80, 300), 2),
            keyboard_flight_std=round(random.uniform(30, 120), 2),
            typing_speed_wpm=round(random.uniform(30, 90), 1),
            keyboard_error_rate=round(random.uniform(0.01, 0.08), 3),
            keyboard_backspace_rate=round(random.uniform(0.02, 0.1), 3),
            touch_pressure_mean=round(random.uniform(0.3, 0.7), 3),
            touch_area_mean=round(random.uniform(50, 150), 1),
            touch_orientation_mean=round(random.uniform(-5, 5), 1),
            gyroscope_tilt_std=round(random.uniform(5, 30), 2),
            accelerometer_magnitude_mean=round(random.uniform(9.5, 11.0), 2),
            behavioral_consistency_score=round(random.uniform(0.6, 1.0), 3),
            anomaly_score=round(random.uniform(0.0, 0.3), 3),
        )


@dataclass
class AdvancedPaymentTelemetry:
    """Master telemetry class combining all signals and ISO 20022 fields."""
    three_ds_context: ThreeDS2Context = field(default_factory=ThreeDS2Context)
    tls_fingerprint: TLSFingerprint = field(default_factory=TLSFingerprint)
    browser_fingerprint: BrowserFingerprint = field(default_factory=BrowserFingerprint)
    behavioral_biometrics: BehavioralBiometrics = field(default_factory=BehavioralBiometrics)
    instruction_id: str = ""
    end_to_end_id: str = ""
    uetr: str = ""
    debtor_name: str = ""
    debtor_account_id: str = ""
    creditor_name: str = ""
    creditor_account_id: str = ""
    ip_address: str = ""
    geo_lat: float = 0.0
    geo_long: float = 0.0
    asn: int = 0
    isp: str = ""
    velocity_score: float = 0.0
    device_trust_score: float = 0.0
    geo_risk_score: float = 0.0

    def to_ml_features(self) -> Dict[str, Any]:
        """Flatten all telemetry into a single dict for ML model input."""
        features: Dict[str, Any] = {}
        ds = self.three_ds_context.to_dict()
        for key, val in ds.items():
            features[f"3ds_{key}"] = val.value if isinstance(val, Enum) else val
        for prefix, obj, attrs in [
            ("tls", self.tls_fingerprint, [
                "ja3_hash", "ja3_raw", "ja4_hash", "ja4_raw", "tls_version",
                "cipher_suite_count", "extension_count", "has_alpn",
                "supports_http2", "signature_algorithm",
            ]),
            ("bf", self.browser_fingerprint, [
                "canvas_hash", "webgl_hash", "audio_hash", "webrtc_ip",
                "platform", "language", "hardware_concurrency", "device_memory",
                "plugins_count", "has_adblock", "fingerprint_entropy",
            ]),
        ]:
            for attr in attrs:
                features[f"{prefix}_{attr}"] = getattr(obj, attr)
        for attr in vars(self.behavioral_biometrics):
            features[f"behav_{attr}"] = getattr(self.behavioral_biometrics, attr)
        for attr in [
            "instruction_id", "end_to_end_id", "uetr",
            "debtor_name", "debtor_account_id",
            "creditor_name", "creditor_account_id",
            "ip_address", "geo_lat", "geo_long", "asn", "isp",
            "velocity_score", "device_trust_score", "geo_risk_score",
        ]:
            features[f"tx_{attr}"] = getattr(self, attr)
        return features

    @classmethod
    def generate_mock(cls, is_fraud: bool = False) -> "AdvancedPaymentTelemetry":
        """Generate a complete mock telemetry record.

        Args:
            is_fraud: If True, injects fraudulent signals across all subsystems.
        """
        ip_parts = [str(random.randint(1, 254)) for _ in range(4)]
        return cls(
            three_ds_context=ThreeDS2Context(
                sdk_app_id=uuid.uuid4().hex[:16],
                sdk_transaction_id=str(uuid.uuid4()),
                sdk_ephemeral_public_key=uuid.uuid4().hex,
                user_agent="Mozilla/5.0",
                screen_width=random.choice([1366, 1920, 2560]),
                screen_height=random.choice([768, 1080, 1440]),
                timezone_offset=random.randint(-720, 720),
                java_enabled=random.random() < 0.3,
            ),
            tls_fingerprint=TLSFingerprint.generate_mock(),
            browser_fingerprint=BrowserFingerprint.generate_mock(),
            behavioral_biometrics=BehavioralBiometrics.generate_mock(is_fraud),
            instruction_id=str(uuid.uuid4()),
            end_to_end_id=str(uuid.uuid4()),
            uetr=str(uuid.uuid4()),
            debtor_name="Acme Corp",
            debtor_account_id="".join(str(random.randint(0, 9)) for _ in range(20)),
            creditor_name="Global Payments",
            creditor_account_id="".join(str(random.randint(0, 9)) for _ in range(20)),
            ip_address=".".join(ip_parts),
            geo_lat=round(random.uniform(-90, 90), 6),
            geo_long=round(random.uniform(-180, 180), 6),
            asn=random.randint(1000, 65535),
            isp=random.choice(["Comcast", "AT&T", "Verizon", "Vodafone", "Deutsche Telekom"]),
            velocity_score=round(random.uniform(0.6, 1.0) if is_fraud else random.uniform(0.0, 0.5), 3),
            device_trust_score=round(random.uniform(0.0, 0.3) if is_fraud else random.uniform(0.5, 1.0), 3),
            geo_risk_score=round(random.uniform(0.7, 1.0) if is_fraud else random.uniform(0.0, 0.4), 3),
        )


class MITRETechnique:
    """A single MITRE ATLAS technique."""
    __slots__ = ("technique_id", "name", "description", "detection")

    def __init__(self, technique_id: str, name: str, description: str, detection: str) -> None:
        self.technique_id = technique_id
        self.name = name
        self.description = description
        self.detection = detection


class MITREATLASMapper:
    """Maps fraud/attack patterns to MITRE ATLAS tactics and techniques."""

    AML_TACTICS: Dict[str, Dict[str, Any]] = {
        "AML.T0010": {
            "tactic_id": "AML.T0010", "name": "Resource Development",
            "description": "Adversaries establish resources to support operations.",
            "techniques": [
                {"id": "AML.T0010.001", "name": "Acquire Infrastructure",
                 "desc": "Adversaries acquire domains, IPs, or servers for staging.",
                 "detection": "Monitor for anomalous domain registrations or IP purchases."},
                {"id": "AML.T0010.002", "name": "Compromise Accounts",
                 "desc": "Adversaries take over legitimate accounts for use in attacks.",
                 "detection": "Detect impossible travel and credential stuffing patterns."},
            ],
        },
        "AML.T0011": {
            "tactic_id": "AML.T0011", "name": "Initial Access",
            "description": "Adversaries gain initial foothold into target systems.",
            "techniques": [
                {"id": "AML.T0011.001", "name": "Phishing",
                 "desc": "Adversaries send fraudulent messages to steal credentials.",
                 "detection": "Monitor for suspicious email attachments and credential harvest pages."},
                {"id": "AML.T0011.002", "name": "Exploit Public-Facing Application",
                 "desc": "Adversaries exploit vulnerabilities in internet-facing services.",
                 "detection": "Alert on unusual request patterns and WAF rule violations."},
            ],
        },
        "AML.T0020": {
            "tactic_id": "AML.T0020", "name": "Evasion",
            "description": "Adversaries avoid detection by security controls.",
            "techniques": [
                {"id": "AML.T0020.001", "name": "Obfuscated Files or Information",
                 "desc": "Adversaries conceal malicious payloads via encoding.",
                 "detection": "Analyze file entropy and known obfuscation signatures."},
                {"id": "AML.T0020.002", "name": "Indicator Removal",
                 "desc": "Adversaries delete logs and forensic artifacts.",
                 "detection": "Monitor for log deletion and suspicious cleanup commands."},
            ],
        },
        "AML.T0025": {
            "tactic_id": "AML.T0025", "name": "Credential Access",
            "description": "Adversaries steal account credentials and secrets.",
            "techniques": [
                {"id": "AML.T0025.001", "name": "Credential Dumping",
                 "desc": "Adversaries extract credentials from memory or storage.",
                 "detection": "Monitor for LSASS access and unusual memory reads."},
                {"id": "AML.T0025.002", "name": "Brute Force",
                 "desc": "Adversaries guess passwords via systematic attempts.",
                 "detection": "Alert on high-volume failed authentication attempts."},
            ],
        },
        "AML.T0035": {
            "tactic_id": "AML.T0035", "name": "Lateral Movement",
            "description": "Adversaries move laterally across the network.",
            "techniques": [
                {"id": "AML.T0035.001", "name": "Remote Services",
                 "desc": "Adversaries abuse remote access protocols to pivot.",
                 "detection": "Track unusual SSH, RDP, or SMB connections between hosts."},
                {"id": "AML.T0035.002", "name": "Use Alternate Authentication Material",
                 "desc": "Adversaries leverage tokens or pass-the-hash techniques.",
                 "detection": "Detect token reuse and NTLM relay patterns."},
            ],
        },
        "AML.T0051": {
            "tactic_id": "AML.T0051", "name": "LLM Prompt Injection",
            "description": "Adversaries inject malicious prompts into LLM interactions.",
            "techniques": [
                {"id": "AML.T0051.001", "name": "Direct Prompt Injection",
                 "desc": "Adversaries craft prompts that override LLM instructions.",
                 "detection": "Monitor for adversarial prompt patterns in user inputs."},
                {"id": "AML.T0051.002", "name": "Indirect Prompt Injection",
                 "desc": "Adversaries embed payloads in external data consumed by LLMs.",
                 "detection": "Scan ingested documents for hidden instructions."},
            ],
        },
        "AML.T0054": {
            "tactic_id": "AML.T0054", "name": "LLM Jailbreaking",
            "description": "Adversaries bypass LLM safety guardrails.",
            "techniques": [
                {"id": "AML.T0054.001", "name": "Role Playing Attack",
                 "desc": "Adversaries instruct LLM to assume unrestricted personas.",
                 "detection": "Flag jailbreak-style system prompt overrides."},
                {"id": "AML.T0054.002", "name": "Payload Injection via Metadata",
                 "desc": "Adversaries hide instructions in document metadata or formatting.",
                 "detection": "Audit document metadata before LLM ingestion."},
            ],
        },
    }

    _ATTACK_CATEGORY_MAP: Dict[str, List[str]] = {
        "account_takeover": ["AML.T0010", "AML.T0011", "AML.T0025"],
        "card_fraud": ["AML.T0011", "AML.T0020", "AML.T0035"],
        "credential_stuffing": ["AML.T0025"],
        "synthetic_identity": ["AML.T0010", "AML.T0011"],
        "money_laundering": ["AML.T0035", "AML.T0020"],
        "prompt_injection": ["AML.T0051"],
        "llm_abuse": ["AML.T0054", "AML.T0051"],
        "web_scraping": ["AML.T0011", "AML.T0020"],
        "bot_attack": ["AML.T0011", "AML.T0025"],
        "insider_threat": ["AML.T0025", "AML.T0035"],
    }

    @classmethod
    def map_attack(cls, attack_category: str) -> List[Dict[str, Any]]:
        """Map an attack category to relevant MITRE ATLAS techniques.

        Args:
            attack_category: A key from the attack category mapping.

        Returns:
            List of tactic dicts containing their matched techniques.
        """
        tactic_ids = cls._ATTACK_CATEGORY_MAP.get(attack_category.lower(), [])
        results: List[Dict[str, Any]] = []
        for tid in tactic_ids:
            tactic = cls.AML_TACTICS.get(tid)
            if tactic:
                results.append({
                    "tactic_id": tactic["tactic_id"],
                    "tactic_name": tactic["name"],
                    "description": tactic["description"],
                    "techniques": [
                        {"technique_id": t["id"], "name": t["name"],
                         "description": t["desc"], "detection": t["detection"]}
                        for t in tactic["techniques"]
                    ],
                })
        return results

    @classmethod
    def get_tactic_details(cls, tactic_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details for a specific tactic.

        Args:
            tactic_id: The tactic ID (e.g., "AML.T0010").

        Returns:
            Tactic details dict, or None if not found.
        """
        tactic = cls.AML_TACTICS.get(tactic_id)
        if not tactic:
            return None
        return {
            "tactic_id": tactic["tactic_id"],
            "name": tactic["name"],
            "description": tactic["description"],
            "techniques": [
                {"technique_id": t["id"], "name": t["name"],
                 "description": t["desc"], "detection": t["detection"]}
                for t in tactic["techniques"]
            ],
        }
