from decimal import Decimal

from bitcoin_utxo_lp import (
    UTXO,
    TxSizing,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
)


def main() -> None:
    utxos = [
        UTXO(
            txid="a" * 64,
            vout=0,
            value_sats=1_000,
            input_vbytes=Decimal("68"),
        ),
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

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver()

    result = solver.solve(model)

    print("Selected UTXOs:", result.selected)
    print("Fee (sats):", result.fee_sats)
    print("Change (sats):", result.change_sats)
    print("Tx size (vB):", result.tx_vbytes)


if __name__ == "__main__":
    main()
