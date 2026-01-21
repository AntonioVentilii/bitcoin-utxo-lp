from importlib.metadata import version, PackageNotFoundError
from .types import (
    SelectionParams,
    SelectionResult,
    TxSizing,
    UTXO,
)
from .model import SimpleCoinSelectionModel
from .solver import SimpleMILPSolver


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
