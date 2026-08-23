"""
Threat Intelligence Generator
Automated attack vector synthesis and MITRE ATLAS mapping for payment security
"""

import json
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .taxonomy_schema import (
    AttackVector, AttackCategory, RiskLevel, PaymentChannel,
    AttackPrecondition, AttackStep, ThreatTaxonomy
)


class ThreatIntelGenerator:
    """
    Generates synthetic attack vectors for payment security red teaming
    
    Features:
    - Pre-defined GenAI-powered attack patterns
    - MITRE ATLAS mapping for payment systems
    - Dynamic attack vector synthesis
    - Risk scoring and fidelity assessment
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed for reproducibility"""
        if seed is not None:
            random.seed(seed)
        self.taxonomy = ThreatTaxonomy(
            version="1.0.0",
            last_updated=datetime.now().isoformat()
        )
        self._initialize_base_vectors()

    def _initialize_base_vectors(self) -> None:
        """Initialize the base set of GenAI-powered attack vectors"""
        
        # Vector 1: Synthetic Identity & Persona Orchestration
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-001",
            name="LLM-Driven Synthetic Identity Orchestrator",
            category=AttackCategory.SYNTHETIC_IDENTITY,
            risk_level=RiskLevel.CRITICAL,
            description=(
                "Autonomous AI agent generates coordinated synthetic identities with "
                "realistic credit histories, social media footprints, and device profiles. "
                "Exploits KYC onboarding gaps across multiple financial institutions."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Access to generative LLM with financial persona training",
                    required_access="LLM API or local model",
                    target_component="KYC/Onboarding System",
                    estimated_difficulty=6
                ),
                AttackPrecondition(
                    description="Proxy network for multi-channel account creation",
                    required_access="Residential proxy pool",
                    target_component="Account Registration APIs",
                    estimated_difficulty=4
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Generate synthetic persona (name, DOB, SSN, address)",
                    iso20022_fields=["Cdtr/CdtrId/PrvtId/Othr/Id"],
                    iso8583_fields=["Field 37", "Field 48"],
                    evasion_technique="Benford's Law compliant amount generation"
                ),
                AttackStep(
                    step_id=2,
                    description="Create realistic device fingerprint cluster",
                    iso20022_fields=["SctiesTx/DvcTp"],
                    evasion_technique="Device fingerprint rotation with consistent hardware profile"
                ),
                AttackStep(
                    step_id=3,
                    description="Establish credit history via synthetic tradelines",
                    iso20022_fields=["TradRegData"],
                    evasion_technique="Gradual credit building over simulated 6-month window"
                ),
                AttackStep(
                    step_id=4,
                    description="Execute multi-institution account takeover",
                    iso20022_fields=["Acct/CdAcct"],
                    evasion_technique="Velocity distributed across 50+ institutions"
                )
            ],
            target_channels=[PaymentChannel.ECOMMERCE, PaymentChannel.MOBILE_WALLET],
            fidelity_score=0.92,
            bypass_probability=0.45,
            mitre_atlas_mapping=["AML.T0010.000", "AML.T0011.001"]
        ))

        # Vector 2: Multi-Hop CNP Agentic Relay
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-002",
            name="Autonomous CNP Relay Agent",
            category=AttackCategory.MULTI_HOP_CNP,
            risk_level=RiskLevel.CRITICAL,
            description=(
                "AI purchasing agent exploits merchant checkout APIs via proxy networks, "
                "executing card-not-present transactions through multi-hop relay chains "
                "to evade velocity controls and geolocation checks."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Compromised or synthetic card credentials",
                    required_access="Card data (fullz or BIN + last4)",
                    target_component="Card Authorization System",
                    estimated_difficulty=5
                ),
                AttackPrecondition(
                    description="Distributed proxy network with geo-diversity",
                    required_access="500+ residential proxies",
                    target_component="Merchant Checkout API",
                    estimated_difficulty=4
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Initialize agentic purchasing framework",
                    iso20022_fields=["StmtlDt"],
                    iso8583_fields=["Field 7", "Field 11"],
                    evasion_technique="Session-based isolation per transaction"
                ),
                AttackStep(
                    step_id=2,
                    description="Route through multi-hop proxy chain",
                    iso20022_fields=["RmtInf/Inv/Dt"],
                    evasion_technique="Geo-consistent proxy rotation per card profile"
                ),
                AttackStep(
                    step_id=3,
                    description="Execute distributed micro-transactions",
                    iso20022_fields=["CdtTx/InstdAmt"],
                    iso8583_fields=["Field 4", "Field 37"],
                    evasion_technique="Below-threshold amounts ($5-$50) with random intervals"
                ),
                AttackStep(
                    step_id=4,
                    description="Aggregate and extract via mule network",
                    iso20022_fields=["CdtrAcct/Id/IBAN"],
                    evasion_technique="Legitimate-looking refund patterns"
                )
            ],
            target_channels=[PaymentChannel.ECOMMERCE, PaymentChannel.CNP],
            fidelity_score=0.88,
            bypass_probability=0.52,
            mitre_atlas_mapping=["AML.T0010.002", "AML.T0012.001"]
        ))

        # Vector 3: Prompt Injection into Merchant LLM
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-003",
            name="LLM Payment Gateway Injection",
            category=AttackCategory.PROMPT_INJECTION,
            risk_level=RiskLevel.HIGH,
            description=(
                "Exploits conversational commerce and AI payment assistants via prompt "
                "injection to alter transaction routing, bypass amount limits, or "
                "exfiltrate sensitive payment data through manipulated responses."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Identified merchant using LLM for payment assistance",
                    required_access="Merchant chat interface",
                    target_component="LLM Payment Assistant",
                    estimated_difficulty=5
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Enumerate merchant LLM capabilities",
                    iso20022_fields=["Purp/Cd"],
                    evasion_technique="Natural language probing via chat interface"
                ),
                AttackStep(
                    step_id=2,
                    description="Inject system prompt override",
                    iso20022_fields=["RmtInf/Ustrd"],
                    evasion_technique="Encoded payload in transaction description"
                ),
                AttackStep(
                    step_id=3,
                    description="Manipulate transaction routing parameters",
                    iso20022_fields=["PmtInf/SttlmInf"],
                    evasion_technique="Subtle field manipulation in confirmation response"
                ),
                AttackStep(
                    step_id=4,
                    description="Extract card data via side-channel in LLM response",
                    iso20022_fields=["CardData/PAN"],
                    evasion_technique="Data exfiltration through natural language response"
                )
            ],
            target_channels=[PaymentChannel.ECOMMERCE, PaymentChannel.MOBILE_WALLET],
            fidelity_score=0.78,
            bypass_probability=0.38,
            mitre_atlas_mapping=["AML.T0051.000", "AML.T0054.001"]
        ))

        # Vector 4: Voice Deepfake & Automated Vishing
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-004",
            name="AI Voice Clone Authentication Bypass",
            category=AttackCategory.VOICE_DEEPFAKE,
            risk_level=RiskLevel.HIGH,
            description=(
                "Uses AI-generated voice clones to bypass voice-based MFA and "
                "out-of-band authentication. Automates vishing campaigns targeting "
                "high-value accounts with personalized social engineering."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Target voice sample (3-10 seconds)",
                    required_access="Voice recording from public sources",
                    target_component="Voice Authentication System",
                    estimated_difficulty=6
                ),
                AttackPrecondition(
                    description="Real-time voice synthesis capability",
                    required_access="Voice cloning API or local model",
                    target_component="Phone Banking System",
                    estimated_difficulty=7
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Harvest target voice samples from public media",
                    iso20022_fields=["Dbtr/ctctDtls"],
                    evasion_technique="Multiple sample aggregation for consistency"
                ),
                AttackStep(
                    step_id=2,
                    description="Generate high-fidelity voice clone",
                    iso20022_fields=["AuthnTp"],
                    evasion_technique="Emotional context matching for naturalness"
                ),
                AttackStep(
                    step_id=3,
                    description="Execute automated vishing call",
                    iso20022_fields=["SctiesTx/SctiesAcct"],
                    evasion_technique="Scripted conversation with dynamic responses"
                ),
                AttackStep(
                    step_id=4,
                    description="Capture and relay OTP/verification codes",
                    iso20022_fields=["TxDtTm"],
                    evasion_technique="Real-time DTMF detection and relay"
                )
            ],
            target_channels=[PaymentChannel.CNP, PaymentChannel.P2P],
            fidelity_score=0.85,
            bypass_probability=0.42,
            mitre_atlas_mapping=["AML.T0012.002", "AML.T0035.001"]
        ))

        # Vector 5: Merchant API Abuse
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-005",
            name="Aggressive Bot Checkout Exploitation",
            category=AttackCategory.MERCHANT_API_ABUSE,
            risk_level=RiskLevel.HIGH,
            description=(
                "Autonomous AI agents exploit merchant checkout APIs through "
                "race conditions, inventory manipulation, and payment callback "
                "exploitation to obtain goods without valid payment."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Merchant API endpoint enumeration",
                    required_access="Public API documentation",
                    target_component="Checkout API",
                    estimated_difficulty=3
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Map merchant checkout flow and API endpoints",
                    iso20022_fields=["CreDtTm"],
                    evasion_technique="Low-frequency probing to avoid rate limits"
                ),
                AttackStep(
                    step_id=2,
                    description="Identify race condition in inventory reservation",
                    iso20022_fields=["SttlmPrd"],
                    evasion_technique="Concurrent request flooding with session isolation"
                ),
                AttackStep(
                    step_id=3,
                    description="Execute payment callback manipulation",
                    iso20022_fields=["PmtInf/PmtInfId"],
                    evasion_technique="Forged webhook with valid signature algorithm"
                ),
                AttackStep(
                    step_id=4,
                    description="Fulfill order with invalid payment",
                    iso20022_fields=["SttlmDt"],
                    evasion_technique="Delayed detection window exploitation"
                )
            ],
            target_channels=[PaymentChannel.ECOMMERCE],
            fidelity_score=0.82,
            bypass_probability=0.35,
            mitre_atlas_mapping=["AML.T0010.001", "AML.T0011.002"]
        ))

        # Vector 6: Velocity Evasion
        self.taxonomy.add_vector(AttackVector(
            vector_id="ATK-006",
            name="Adaptive Velocity Control Evasion",
            category=AttackCategory.VELOCITY_EVASION,
            risk_level=RiskLevel.MEDIUM,
            description=(
                "Machine learning-guided transaction timing optimization that "
                "learns velocity control thresholds and distributes transactions "
                "to maximize volume while staying below detection thresholds."
            ),
            preconditions=[
                AttackPrecondition(
                    description="Sample of historical transaction approvals",
                    required_access="Transaction logs or BIN data",
                    target_component="Velocity Control System",
                    estimated_difficulty=5
                )
            ],
            execution_steps=[
                AttackStep(
                    step_id=1,
                    description="Analyze velocity control patterns",
                    iso20022_fields=["TxDtTm"],
                    evasion_technique="Statistical analysis of approval patterns"
                ),
                AttackStep(
                    step_id=2,
                    description="Train timing optimization model",
                    iso20022_fields=["CreDtTm"],
                    evasion_technique="Reinforcement learning for optimal spacing"
                ),
                AttackStep(
                    step_id=3,
                    description="Execute distributed transactions",
                    iso20022_fields=["CdtTx/InstdAmt"],
                    evasion_technique="Probabilistic timing with noise injection"
                )
            ],
            target_channels=[PaymentChannel.ECOMMERCE, PaymentChannel.CNP],
            fidelity_score=0.75,
            bypass_probability=0.48,
            mitre_atlas_mapping=["AML.T0010.003"]
        ))

    def synthesize_novel_variant(
        self, 
        base_vector_id: str, 
        mutation_rate: float = 0.3
    ) -> AttackVector:
        """
        Generate a novel attack variant by mutating an existing vector
        
        Args:
            base_vector_id: ID of the base vector to mutate
            mutation_rate: Probability of mutating each attribute (0-1)
        
        Returns:
            New AttackVector with mutations applied
        """
        base = next(
            (v for v in self.taxonomy.vectors if v.vector_id == base_vector_id),
            None
        )
        if not base:
            raise ValueError(f"Vector {base_vector_id} not found")

        # Generate new ID
        new_id = f"ATK-{hashlib.md5(f'{base.vector_id}-{datetime.now().isoformat()}'.encode()).hexdigest()[:6].upper()}"
        
        # Mutate risk level
        new_risk = base.risk_level
        if random.random() < mutation_rate:
            risk_values = list(RiskLevel)
            new_risk = random.choice(risk_values)

        # Mutate fidelity and bypass scores
        new_fidelity = max(0.1, min(1.0, 
            base.fidelity_score + random.gauss(0, 0.1)
        ))
        new_bypass = max(0.0, min(0.95,
            base.bypass_probability + random.gauss(0, 0.08)
        ))

        # Create mutated steps
        mutated_steps = []
        for step in base.execution_steps:
            if random.random() < mutation_rate:
                # Add evasion variation
                new_technique = step.evasion_technique
                if new_technique:
                    variations = [
                        f"{new_technique} with timing jitter",
                        f"Enhanced {new_technique}",
                        f"{new_technique} using distributed approach"
                    ]
                    new_technique = random.choice(variations)
                
                mutated_steps.append(AttackStep(
                    step_id=step.step_id,
                    description=step.description,
                    iso20022_fields=step.iso20022_fields.copy(),
                    iso8583_fields=step.iso8583_fields.copy() if step.iso8583_fields else [],
                    evasion_technique=new_technique
                ))
            else:
                mutated_steps.append(step)

        variant = AttackVector(
            vector_id=new_id,
            name=f"Variant: {base.name}",
            category=base.category,
            risk_level=new_risk,
            description=f"[MUTATED] {base.description}",
            preconditions=base.preconditions.copy(),
            execution_steps=mutated_steps,
            target_channels=base.target_channels.copy(),
            fidelity_score=round(new_fidelity, 3),
            bypass_probability=round(new_bypass, 3),
            mitre_atlas_mapping=base.mitre_atlas_mapping.copy()
        )

        self.taxonomy.add_vector(variant)
        return variant

    def generate_batch(
        self, 
        count: int, 
        categories: Optional[List[AttackCategory]] = None
    ) -> List[AttackVector]:
        """
        Generate a batch of attack vectors
        
        Args:
            count: Number of vectors to generate
            categories: Optional filter for specific categories
        
        Returns:
            List of generated attack vectors
        """
        source_vectors = self.taxonomy.vectors
        if categories:
            source_vectors = [
                v for v in source_vectors 
                if v.category in categories
            ]

        generated = []
        for _ in range(count):
            base = random.choice(source_vectors)
            variant = self.synthesize_novel_variant(
                base.vector_id, 
                mutation_rate=random.uniform(0.2, 0.5)
            )
            generated.append(variant)

        return generated

    def export_taxonomy(self, output_path: str) -> None:
        """Export taxonomy to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(self.taxonomy.to_json())

    def get_statistics(self) -> Dict:
        """Get summary statistics of the taxonomy"""
        vectors = self.taxonomy.vectors
        return {
            "total_vectors": len(vectors),
            "by_category": {
                cat.value: len([v for v in vectors if v.category == cat])
                for cat in AttackCategory
            },
            "by_risk_level": {
                level.value: len([v for v in vectors if v.risk_level == level])
                for level in RiskLevel
            },
            "avg_fidelity": round(
                sum(v.fidelity_score for v in vectors) / max(len(vectors), 1), 3
            ),
            "avg_bypass_probability": round(
                sum(v.bypass_probability for v in vectors) / max(len(vectors), 1), 3
            ),
            "overall_risk_score": self.taxonomy.calculate_overall_risk_score()
        }
