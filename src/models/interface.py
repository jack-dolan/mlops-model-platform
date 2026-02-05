"""Abstract interface for ML models."""

from abc import ABC, abstractmethod
from typing import Any


class ModelInterface(ABC):
    """Base class for all model implementations.

    Any model you want to serve needs to implement these methods.
    This keeps the API code decoupled from specific model details.
    """

    @abstractmethod
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Run inference on input features.

        Args:
            features: dict of feature_name -> value

        Returns:
            dict with prediction, confidence, etc.
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata.

        Returns:
            dict with name, version, features, etc.
        """
        pass
