from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


@dataclass(frozen=True, slots=True)
class Objective:
    fee_sats: int
    tx_vbytes: int


def _evaluate_objective(
    *,
    params: SelectionParams,
    utxos: list[UTXO],
    selected_mask: list[bool],
) -> Objective | None:
    selected = [u for u, take in zip(utxos, selected_mask) if take]
    if not selected:
        return None

    # Simple model ALWAYS includes change output.
    fixed_vb = (
        params.sizing.base_overhead_vbytes
        + params.sizing.recipient_output_vbytes
        + params.sizing.change_output_vbytes
    )
    vbytes = fixed_vb + sum(u.input_vbytes for u in selected)
    tx_vbytes = math.ceil(vbytes)
    fee_sats = math.ceil(params.fee_rate_sat_per_vb * tx_vbytes)

    total_in = sum(u.value_sats for u in selected)
    change = total_in - params.target_sats - fee_sats

    if change < params.min_change_sats:
        return None
    if total_in != params.target_sats + fee_sats + change:
        return None

    return Objective(fee_sats=fee_sats, tx_vbytes=tx_vbytes)


def _best_by_exhaustive_search(
    *,
    params: SelectionParams,
    utxos: list[UTXO],
) -> tuple[Objective, list[UTXO]]:
    best_obj: Objective | None = None
    best_sel: list[UTXO] | None = None

    for bits in itertools.product([False, True], repeat=len(utxos)):
        obj = _evaluate_objective(params=params, utxos=utxos, selected_mask=list(bits))
        if obj is None:
            continue
        selected = [u for u, take in zip(utxos, bits) if take]

        if best_obj is None:
            best_obj, best_sel = obj, selected
            continue

        # Primary objective: minimise fee
        if obj.fee_sats < best_obj.fee_sats:
            best_obj, best_sel = obj, selected
            continue

        # Tie-breaker:
        # fewer vbytes (equivalently fewer inputs) is a reasonable stable tie-break
        if obj.fee_sats == best_obj.fee_sats and obj.tx_vbytes < best_obj.tx_vbytes:
            best_obj, best_sel = obj, selected

    if best_obj is None or best_sel is None:
        raise RuntimeError("No feasible subset found for exhaustive check")
    return best_obj, best_sel


def test_exhaustive_optimality_small_instance() -> None:
    utxos = [
        UTXO("a" * 64, 0, 40_000, 68.0),
        UTXO("b" * 64, 1, 30_000, 68.0),
        UTXO("c" * 64, 2, 25_000, 58.0),
        UTXO("d" * 64, 3, 12_000, 91.0),
        UTXO("e" * 64, 4, 60_000, 68.0),
        UTXO("f" * 64, 5, 15_000, 148.0),
        UTXO("0" * 64, 6, 18_000, 68.0),
        UTXO("1" * 64, 7, 22_000, 58.0),
        UTXO("2" * 64, 8, 9_000, 91.0),
        UTXO("3" * 64, 9, 50_000, 68.0),
    ]

    params = SelectionParams(
        target_sats=95_000,
        fee_rate_sat_per_vb=3.0,
        min_change_sats=546,
        sizing=TxSizing(
            base_overhead_vbytes=10.0,
            recipient_output_vbytes=31.0,
            change_output_vbytes=31.0,
        ),
    )

    best_obj, _best_sel = _best_by_exhaustive_search(params=params, utxos=utxos)

    res = SimpleMILPSolver(time_limit_seconds=10).solve(
        SimpleCoinSelectionModel(utxos=utxos, params=params)
    )

    assert res.fee_sats == best_obj.fee_sats
    assert res.tx_vbytes == best_obj.tx_vbytes
