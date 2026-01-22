from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


def main() -> None:
    utxos = [
        # One UTXO that's *above* the target, but not enough after fees.
        UTXO(txid="A" * 64, vout=0, value_sats=83_200, input_vbytes=68.0),
        # Small top-ups (each below target)
        UTXO(txid="B" * 64, vout=1, value_sats=2_000, input_vbytes=68.0),
        UTXO(txid="C" * 64, vout=2, value_sats=1_200, input_vbytes=58.0),
        # Some decoys
        UTXO(
            txid="D" * 64, vout=3, value_sats=84_000, input_vbytes=148.0
        ),  # expensive input
        UTXO(txid="E" * 64, vout=4, value_sats=10_000, input_vbytes=91.0),
    ]

    params = SelectionParams(
        target_sats=83_000,
        fee_rate_sat_per_vb=5.0,
        min_change_sats=546,
        sizing=TxSizing(
            base_overhead_vbytes=10.0,
            recipient_output_vbytes=31.0,
            change_output_vbytes=31.0,
        ),
    )

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver(time_limit_seconds=5)
    result = solver.solve(model)

    print("Selected UTXOs:")
    for u in result.selected:
        print(
            f"  - {u.txid[:8]}...:{u.vout} "
            f"value={u.value_sats} sats "
            f"input_vbytes={u.input_vbytes}"
        )

    print("\nFee (sats):", result.fee_sats)
    print("Change (sats):", result.change_sats)
    print("Tx size (vB):", result.tx_vbytes)
    print("Total input (sats):", result.total_input_sats)
    print("Target (sats):", params.target_sats)


if __name__ == "__main__":
    main()
