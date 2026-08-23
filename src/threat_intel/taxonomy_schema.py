"""
Taxonomy Schema for Payment Security Threat Intelligence
MITRE ATLAS-aligned attack vector definitions for GenAI-powered fraud
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


class AttackCategory(Enum):
    """MITRE ATLAS-aligned attack categories for payment systems"""
    SYNTHETIC_IDENTITY = "synthetic_identity"
    MULTI_HOP_CNP = "multi_hop_cnp"
    PROMPT_INJECTION = "prompt_injection"
    VOICE_DEEPFAKE = "voice_deepfake"
    ACCOUNT_TAKEOVER = "account_takeover"
    MERCHANT_API_ABUSE = "merchant_api_abuse"
    VELOCITY_EVASION = "velocity_evasion"
    GEO_SPOOFING = "geo_spoofing"


class RiskLevel(Enum):
    """Risk impact classification"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class PaymentChannel(Enum):
    """Payment channel targets"""
    ECOMMERCE = "ecommerce"
    POS = "pos"
    MOBILE_WALLET = "mobile_wallet"
    CNP = "cnp"
    P2P = "p2p"
    B2B = "b2b"


@dataclass
class AttackPrecondition:
    """Preconditions required for attack execution"""
    description: str
    required_access: str
    target_component: str
    estimated_difficulty: int  # 1-10 scale


@dataclass
class AttackStep:
    """Individual step in attack execution"""
    step_id: int
    description: str
    iso20022_fields: List[str] = field(default_factory=list)
    iso8583_fields: List[str] = field(default_factory=list)
    evasion_technique: Optional[str] = None


@dataclass
class AttackVector:
    """
    Complete attack vector definition aligned with MITRE ATLAS
    
    Attributes:
        vector_id: Unique identifier for the attack vector
        name: Human-readable attack name
        category: Attack category classification
        risk_level: Risk impact level
        preconditions: Required preconditions for execution
        execution_steps: Ordered list of attack steps
        target_channels: Payment channels targeted
        fidelity_score: How realistic the attack simulation is (0-1)
        bypass_probability: Estimated probability of bypassing current defenses
        mitre_atlas_mapping: MITRE ATLAS technique IDs
    """
    vector_id: str
    name: str
    category: AttackCategory
    risk_level: RiskLevel
    description: str
    preconditions: List[AttackPrecondition]
    execution_steps: List[AttackStep]
    target_channels: List[PaymentChannel]
    fidelity_score: float = 0.85
    bypass_probability: float = 0.3
    mitre_atlas_mapping: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "vector_id": self.vector_id,
            "name": self.name,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "preconditions": [
                {
                    "description": p.description,
                    "required_access": p.required_access,
                    "target_component": p.target_component,
                    "estimated_difficulty": p.estimated_difficulty
                } for p in self.preconditions
            ],
            "execution_steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "iso20022_fields": s.iso20022_fields,
                    "iso8583_fields": s.iso8583_fields,
                    "evasion_technique": s.evasion_technique
                } for s in self.execution_steps
            ],
            "target_channels": [c.value for c in self.target_channels],
            "fidelity_score": self.fidelity_score,
            "bypass_probability": self.bypass_probability,
            "mitre_atlas_mapping": self.mitre_atlas_mapping
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AttackVector':
        """Create from dictionary"""
        return cls(
            vector_id=data["vector_id"],
            name=data["name"],
            category=AttackCategory(data["category"]),
            risk_level=RiskLevel(data["risk_level"]),
            description=data["description"],
            preconditions=[
                AttackPrecondition(**p) for p in data["preconditions"]
            ],
            execution_steps=[
                AttackStep(**s) for s in data["execution_steps"]
            ],
            target_channels=[PaymentChannel(c) for c in data["target_channels"]],
            fidelity_score=data.get("fidelity_score", 0.85),
            bypass_probability=data.get("bypass_probability", 0.3),
            mitre_atlas_mapping=data.get("mitre_atlas_mapping", [])
        )


@dataclass
class ThreatTaxonomy:
    """
    Complete threat taxonomy containing all attack vectors
    
    Provides methods for querying, filtering, and analyzing attack vectors
    """
    vectors: List[AttackVector] = field(default_factory=list)
    version: str = "1.0.0"
    last_updated: str = ""

    def add_vector(self, vector: AttackVector) -> None:
        """Add an attack vector to the taxonomy"""
        self.vectors.append(vector)

    def get_by_category(self, category: AttackCategory) -> List[AttackVector]:
        """Filter vectors by category"""
        return [v for v in self.vectors if v.category == category]

    def get_by_risk_level(self, level: RiskLevel) -> List[AttackVector]:
        """Filter vectors by risk level"""
        return [v for v in self.vectors if v.risk_level == level]

    def get_high_risk_vectors(self) -> List[AttackVector]:
        """Get all HIGH and CRITICAL risk vectors"""
        return [v for v in self.vectors if v.risk_level.value >= RiskLevel.HIGH.value]

    def get_by_channel(self, channel: PaymentChannel) -> List[AttackVector]:
        """Filter vectors by target payment channel"""
        return [v for v in self.vectors if channel in v.target_channels]

    def calculate_overall_risk_score(self) -> float:
        """Calculate weighted risk score across all vectors"""
        if not self.vectors:
            return 0.0
        
        total_score = sum(
            v.risk_level.value * v.bypass_probability * v.fidelity_score
            for v in self.vectors
        )
        return round(total_score / len(self.vectors), 4)

    def to_json(self) -> str:
        """Serialize entire taxonomy to JSON"""
        return json.dumps({
            "version": self.version,
            "last_updated": self.last_updated,
            "total_vectors": len(self.vectors),
            "risk_score": self.calculate_overall_risk_score(),
            "vectors": [v.to_dict() for v in self.vectors]
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'ThreatTaxonomy':
        """Deserialize taxonomy from JSON"""
        data = json.loads(json_str)
        taxonomy = cls(
            version=data.get("version", "1.0.0"),
            last_updated=data.get("last_updated", "")
        )
        for v_data in data.get("vectors", []):
            taxonomy.add_vector(AttackVector.from_dict(v_data))
        return taxonomy
