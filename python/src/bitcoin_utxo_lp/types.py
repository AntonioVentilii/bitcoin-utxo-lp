from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class UTXO:
    """A spendable UTXO with known value and estimated input size."""

    txid: str
    vout: int
    value_sats: int
    input_vbytes: float


@dataclass(frozen=True, slots=True)
class TxSizing:
    """
    Transaction sizing constants for a specific transaction template.

    b: base overhead vbytes (version/locktime/counts etc.)
    recipient_output_vbytes: vbytes for the recipient output(s) *total*
    change_output_vbytes: vbytes for the change output
    """

    base_overhead_vbytes: float
    recipient_output_vbytes: float
    change_output_vbytes: float


@dataclass(frozen=True, slots=True)
class SelectionParams:
    """Fixed inputs for one coin-selection run."""

    target_sats: int
    fee_rate_sat_per_vb: float
    min_change_sats: int  # dust / wallet policy threshold
    sizing: TxSizing


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Solution returned by the solver."""

    selected: tuple[UTXO, ...]
    change_sats: int
    fee_sats: int
    tx_vbytes: int

    @property
    def total_input_sats(self) -> int:
        return sum(u.value_sats for u in self.selected)

    @property
    def total_output_sats(self) -> int:
        # recipient + change (fee excluded)
        return self.total_input_sats - self.fee_sats


def total_input_vbytes(selected: Sequence[UTXO]) -> float:
    return sum((u.input_vbytes for u in selected), float(0))
