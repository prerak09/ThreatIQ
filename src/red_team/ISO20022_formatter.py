"""
ISO 20022 Payment Message Formatter
Standardizes transaction payloads for payment rail compatibility
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from .agents import Transaction
except ImportError:
    from red_team.agents import Transaction


@dataclass
class ISO20022Header:
    """ISO 20022 message header"""
    message_id: str
    creation_date_time: str
    message_type: str = "pacs.008.001.08"  # Customer Credit Transfer
    initiating_party: str = "MBRC"
    originating_address: str = "AXISBOMBMC"


@dataclass
class ISO20022CreditTransfer:
    """ISO 20022 Credit Transfer payload"""
    # Payment Identification
    instruction_id: str
    end_to_end_id: str
    uetr: str
    
    # Amount
    instructed_amount: str
    currency: str
    
    # Debtor (sender)
    debtor_name: str
    debtor_account_iban: str
    debtor_agent_bic: str
    
    # Creditor (receiver)
    creditor_name: str
    creditor_account_iban: str
    creditor_agent_bic: str
    
    # Remittance Information
    remittance_info_unstructured: str
    
    # Additional fields
    charge_bearer: str = "DEBT"
    payment_type_info: str = "CARD"
    settlement_method: str = "CLRG"


class ISO20022Formatter:
    """
    Formats transactions into ISO 20022 compliant payment messages
    
    Supports:
    - pacs.008 (Customer Credit Transfer)
    - pacs.002 (Payment Status Report)
    - pain.001 (Customer Credit Transfer Initiation)
    """

    def __init__(self, bank_bic: str = "MASTCRDMC"):
        self.bank_bic = bank_bic
        self._sequence_counter = 0

    def _generate_uetr(self) -> str:
        """Generate UETR (Unique End-to-End Transaction Reference)"""
        import uuid
        return str(uuid.uuid4()).upper()

    def _generate_instruction_id(self) -> str:
        """Generate unique instruction ID"""
        self._sequence_counter += 1
        return f"INSTR-{datetime.now().strftime('%Y%m%d')}-{self._sequence_counter:06d}"

    def _generate_end_to_end_id(self) -> str:
        """Generate end-to-end ID"""
        import uuid
        return f"E2E-{uuid.uuid4().hex[:16].upper()}"

    def _mask_pan(self, last4: str) -> str:
        """Mask PAN for security"""
        return f"****{last4}"

    def format_credit_transfer(
        self,
        transaction: Transaction,
        debtor_name: str = "John Doe",
        creditor_name: str = "Merchant Store",
        debtor_iban: str = "DE89370400440532013000",
        creditor_iban: str = "DE89370400440532013001"
    ) -> Dict[str, Any]:
        """
        Format a transaction as ISO 20022 credit transfer
        
        Args:
            transaction: Transaction object
            debtor_name: Sender name
            creditor_name: Receiver name
            debtor_iban: Sender IBAN
            creditor_iban: Receiver IBAN
        
        Returns:
            ISO 20022 compliant message dictionary
        """
        header = ISO20022Header(
            message_id=f"MSG-{transaction.transaction_id}",
            creation_date_time=transaction.timestamp,
            initiating_party="MBRC",
            originating_address=self.bank_bic
        )

        transfer = ISO20022CreditTransfer(
            instruction_id=self._generate_instruction_id(),
            end_to_end_id=self._generate_end_to_end_id(),
            uetr=self._generate_uetr(),
            instructed_amount=f"{transaction.amount:.2f}",
            currency=transaction.currency,
            debtor_name=debtor_name,
            debtor_account_iban=debtor_iban,
            debtor_agent_bic=self.bank_bic,
            creditor_name=creditor_name,
            creditor_account_iban=creditor_iban,
            creditor_agent_bic=self.bank_bic,
            remittance_info_unstructured=f"Payment for {transaction.merchant_category_code}"
        )

        # Build complete message
        message = {
            "Document": {
                "xmlns": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08",
                "FIToFICstmrCdtTrf": {
                    "GroupHeader": {
                        "MsgId": header.message_id,
                        "CreDtTm": header.creation_date_time,
                        "NbOfTxs": "1",
                        "SttlmInf": {
                            "SttlmMtd": transfer.settlement_method
                        },
                        "InstgAgt": {
                            "FinInstnId": {
                                "BICFI": header.initiating_party
                            }
                        }
                    },
                    "CdtTrfTxInf": {
                        "PmtId": {
                            "InstrId": transfer.instruction_id,
                            "EndToEndId": transfer.end_to_end_id,
                            "UETR": transfer.uetr
                        },
                        "InstdAmt": {
                            "@Ccy": transfer.currency,
                            "#text": transfer.instructed_amount
                        },
                        "Dbtr": {
                            "Nm": transfer.debtor_name
                        },
                        "DbtrAcct": {
                            "Id": {
                                "IBAN": transfer.debtor_account_iban
                            }
                        },
                        "DbtrAgt": {
                            "FinInstnId": {
                                "BICFI": transfer.debtor_agent_bic
                            }
                        },
                        "CdtrAgt": {
                            "FinInstnId": {
                                "BICFI": transfer.creditor_agent_bic
                            }
                        },
                        "Cdtr": {
                            "Nm": transfer.creditor_name
                        },
                        "CdtrAcct": {
                            "Id": {
                                "IBAN": transfer.creditor_account_iban
                            }
                        },
                        "RmtInf": {
                            "Ustrd": [transfer.remittance_info_unstructured]
                        }
                    }
                }
            }
        }

        # Add metadata for fraud analysis
        message["_metadata"] = {
            "transaction_id": transaction.transaction_id,
            "attack_vector_id": transaction.attack_vector_id,
            "is_fraud": transaction.is_fraud,
            "device_fingerprint": transaction.device_fingerprint,
            "ip_address": transaction.ip_address,
            "geo_lat": transaction.geo_lat,
            "geo_long": transaction.geo_long,
            "auth_channel": transaction.auth_channel,
            "behavioral_biometrics_score": transaction.behavioral_biometrics_score
        }

        return message

    def format_payment_status(
        self,
        original_message_id: str,
        status: str = "ACSP",
        reason_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a payment status report (pacs.002)
        
        Args:
            original_message_id: ID of original message
            status: Transaction status (ACSP = Accepted, RJCT = Rejected)
            reason_code: Optional rejection reason
        
        Returns:
            ISO 20022 payment status message
        """
        return {
            "Document": {
                "xmlns": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10",
                "FIToFIStsRpt": {
                    "GroupHeader": {
                        "MsgId": f"STS-{original_message_id}",
                        "CreDtTm": datetime.now().isoformat(),
                        "NbOfTxs": "1"
                    },
                    "TxInfAndSts": {
                        "OriginalMsgId": original_message_id,
                        "TxSts": status,
                        "StsRsnInf": {
                            "Rsn": {
                                "Cd": reason_code
                            }
                        } if reason_code else None
                    }
                }
            }
        }

    def to_xml_string(self, message: Dict[str, Any]) -> str:
        """
        Convert message dictionary to XML string
        
        Args:
            message: ISO 20022 message dictionary
        
        Returns:
            XML formatted string
        """
        try:
            from lxml import etree
            import dicttoxml
            
            # Remove metadata for XML conversion
            xml_message = {k: v for k, v in message.items() if k != "_metadata"}
            
            xml_bytes = dicttoxml.dicttoxml(
                xml_message,
                custom_root="Document",
                attr_type=False
            )
            return xml_bytes.decode('utf-8')
        except ImportError:
            # Fallback to JSON if lxml not available
            return json.dumps(message, indent=2)

    def extract_features_for_ml(self, message: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract ML-ready features from ISO 20022 message
        
        Args:
            message: ISO 20022 message dictionary
        
        Returns:
            Dictionary of numerical features
        """
        try:
            cdt_trf = message["Document"]["FIToFICstmrCdtTrf"]
            tx_inf = cdt_trf["CdtTrfTxInf"]
            
            features = {
                "amount": float(tx_inf["InstdAmt"]["#text"]),
                "instruction_id_length": len(tx_inf["PmtId"]["InstrId"]),
                "has_uetr": 1.0 if tx_inf["PmtId"].get("UETR") else 0.0,
                "iban_length_dbtr": len(tx_inf["DbtrAcct"]["Id"]["IBAN"]),
                "iban_length_cdtr": len(tx_inf["CdtrAcct"]["Id"]["IBAN"]),
                "same_bank": 1.0 if (
                    tx_inf["DbtrAgt"]["FinInstnId"]["BICFI"] == 
                    tx_inf["CdtrAgt"]["FinInstnId"]["BICFI"]
                ) else 0.0,
                "remittance_length": len(tx_inf["RmtInf"]["Ustrd"][0]) if tx_inf["RmtInf"]["Ustrd"] else 0
            }
            
            # Add metadata features if available
            if "_metadata" in message:
                meta = message["_metadata"]
                features.update({
                    "behavioral_score": meta.get("behavioral_biometrics_score", 0.5),
                    "has_geo": 1.0 if meta.get("geo_lat") else 0.0,
                    "has_device_fp": 1.0 if meta.get("device_fingerprint") else 0.0
                })
            
            return features
        except (KeyError, TypeError):
            return {"error": 0.0}
