from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


def main() -> None:
    # All inputs have the same vbytes => same marginal fee per added input.
    utxos = [
        UTXO(txid="a" * 64, vout=0, value_sats=30_000, input_vbytes=68.0),
        UTXO(txid="b" * 64, vout=1, value_sats=25_000, input_vbytes=68.0),
        UTXO(txid="c" * 64, vout=2, value_sats=24_000, input_vbytes=68.0),
        UTXO(txid="d" * 64, vout=3, value_sats=20_000, input_vbytes=68.0),
        # A single "easy" big coin (above target) that would create lots of change.
        UTXO(txid="E" * 64, vout=4, value_sats=100_000, input_vbytes=68.0),
    ]

    params = SelectionParams(
        target_sats=54_000,
        fee_rate_sat_per_vb=1.0,   # keep input fees low
        min_change_sats=1,         # allow tiny change; we just want "avoid huge change"
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
        print(f"  - {u.txid[:8]}...:{u.vout} value={u.value_sats} sats input_vbytes={u.input_vbytes}")

    print("\nFee (sats):", result.fee_sats)
    print("Change (sats):", result.change_sats)
    print("Tx size (vB):", result.tx_vbytes)
    print("Total input (sats):", result.total_input_sats)
    print("Target (sats):", params.target_sats)


if __name__ == "__main__":
    main()
