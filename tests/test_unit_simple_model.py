from __future__ import annotations

import pytest

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


def _default_sizing() -> TxSizing:
    return TxSizing(
        base_overhead_vbytes=10.0,
        recipient_output_vbytes=31.0,
        change_output_vbytes=31.0,
    )


def test_evaluate_fee_and_vbytes_known_case() -> None:
    utxo = UTXO(txid="a" * 64, vout=0, value_sats=1000, input_vbytes=68.0)
    params = SelectionParams(
        target_sats=300,
        fee_rate_sat_per_vb=1.0,
        min_change_sats=1,
        sizing=_default_sizing(),
    )

    model = SimpleCoinSelectionModel(utxos=[utxo], params=params)
    fee_sats, tx_vbytes = model.evaluate_fee_and_vbytes([utxo])

    assert tx_vbytes == 140  # 10 + 31 + 31 + 68
    assert fee_sats == 140  # 1 sat/vB


def test_solver_single_utxo_happy_path() -> None:
    utxo = UTXO(txid="a" * 64, vout=0, value_sats=1000, input_vbytes=68.0)
    params = SelectionParams(
        target_sats=300,
        fee_rate_sat_per_vb=1.0,
        min_change_sats=1,
        sizing=_default_sizing(),
    )

    res = SimpleMILPSolver().solve(SimpleCoinSelectionModel([utxo], params))

    assert len(res.selected) == 1
    assert res.fee_sats == 140
    assert res.change_sats == 560
    assert res.tx_vbytes == 140

    # invariants
    assert res.total_input_sats == params.target_sats + res.fee_sats + res.change_sats
    assert res.change_sats >= params.min_change_sats


def test_infeasible_target_too_large_raises() -> None:
    utxo = UTXO(txid="a" * 64, vout=0, value_sats=1000, input_vbytes=68.0)
    params = SelectionParams(
        target_sats=2000,
        fee_rate_sat_per_vb=1.0,
        min_change_sats=1,
        sizing=_default_sizing(),
    )

    with pytest.raises(RuntimeError):
        SimpleMILPSolver().solve(SimpleCoinSelectionModel([utxo], params))


def test_infeasible_due_to_min_change_raises() -> None:
    # With one 1000 sat input and fee 140,
    # if target=860 => change=0 which violates min_change=1
    utxo = UTXO(txid="a" * 64, vout=0, value_sats=1000, input_vbytes=68.0)
    params = SelectionParams(
        target_sats=860,
        fee_rate_sat_per_vb=1.0,
        min_change_sats=1,
        sizing=_default_sizing(),
    )

    with pytest.raises(RuntimeError):
        SimpleMILPSolver().solve(SimpleCoinSelectionModel([utxo], params))
