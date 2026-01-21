from decimal import Decimal

from bitcoin_utxo_lp import (
    UTXO,
    TxSizing,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
)


def test_single_utxo_simple_case() -> None:
    utxos = [
        UTXO("a" * 64, 0, 1_000, Decimal("68")),
    ]

    params = SelectionParams(
        target_sats=300,
        fee_rate_sat_per_vb=Decimal("1"),
        min_change_sats=1,
        sizing=TxSizing(
            base_overhead_vbytes=Decimal("10"),
            recipient_output_vbytes=Decimal("31"),
            change_output_vbytes=Decimal("31"),
        ),
    )

    result = SimpleMILPSolver().solve(
        SimpleCoinSelectionModel(utxos=utxos, params=params)
    )

    assert result.fee_sats > 0
    assert result.change_sats >= params.min_change_sats
    assert result.total_input_sats == 1_000
