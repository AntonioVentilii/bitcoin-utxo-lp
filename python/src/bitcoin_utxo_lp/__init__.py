from importlib.metadata import PackageNotFoundError, version

from .model import SimpleCoinSelectionModel
from .solver import SimpleMILPSolver
from .types import (
    UTXO,
    SelectionParams,
    SelectionResult,
    TxSizing,
)

try:
    __version__ = version("bitcoin-utxo-lp")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"


__all__ = [
    "UTXO",
    "TxSizing",
    "SelectionParams",
    "SelectionResult",
    "SimpleCoinSelectionModel",
    "SimpleMILPSolver",
]
