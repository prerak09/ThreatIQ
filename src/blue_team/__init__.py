"""Blue Team module for Mastercard AI Red Teaming Challenge.

Provides fraud detection models, feature engineering pipelines, and
active learning loops for continuous adversarial model improvement.
"""

try:
    from src.blue_team.gnn_model import FraudDetectionModel, PredictionResult
    from src.blue_team.feature_pipeline import FeaturePipeline
    from src.blue_team.active_learning_loop import ActiveLearningLoop
    from src.blue_team.xai_module import (
        SHAPExplainer, FraudExplanation, ExplanationEngine,
        SARGenerator, SARQueue,
    )
except ImportError:
    from .gnn_model import FraudDetectionModel, PredictionResult
    from .feature_pipeline import FeaturePipeline
    from .active_learning_loop import ActiveLearningLoop
    from .xai_module import (
        SHAPExplainer, FraudExplanation, ExplanationEngine,
        SARGenerator, SARQueue,
    )

__all__ = [
    "FraudDetectionModel",
    "PredictionResult",
    "FeaturePipeline",
    "ActiveLearningLoop",
    "SHAPExplainer",
    "FraudExplanation",
    "ExplanationEngine",
    "SARGenerator",
    "SARQueue",
]
