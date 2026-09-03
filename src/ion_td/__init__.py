"""ion_Td: 五唑离子盐热分解温度的可复现实验性评估。"""

from .config import PredictionConfig, load_config
from .dataset import PENTAZOLATE_SMILES, TrainingRecord, load_training_records
from .model import (
    ApplicabilityError,
    PredictionResult,
    ValidationResult,
    predict_temperature,
    validate_model,
)

__version__ = "0.1.0"

__all__ = [
    "ApplicabilityError",
    "PENTAZOLATE_SMILES",
    "PredictionConfig",
    "PredictionResult",
    "TrainingRecord",
    "ValidationResult",
    "load_config",
    "load_training_records",
    "predict_temperature",
    "validate_model",
]
