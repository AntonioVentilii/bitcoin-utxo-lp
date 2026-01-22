import time

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


def main() -> None:
    utxos = [
        UTXO(
            txid=f"{i:064x}",
            vout=0,
            value_sats=10_000 + (i % 3) * 200,  # tiny variance
            input_vbytes=68.0 + (i % 2) * 2.0,  # tiny variance
        )
        for i in range(1_000_000)
    ]

    params = SelectionParams(
        # Forces selecting ~9–10 inputs, but many combinations exist
        target_sats=90_000,
        fee_rate_sat_per_vb=2.5,
        min_change_sats=546,
        sizing=TxSizing(
            base_overhead_vbytes=10.0,
            recipient_output_vbytes=31.0,
            change_output_vbytes=31.0,
        ),
    )

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)

    # Try tightening / loosening this to see the explosion
    solver = SimpleMILPSolver(time_limit_seconds=5)

    start = time.perf_counter()
    result = solver.solve(model)
    elapsed = time.perf_counter() - start

    print(f"Selected {len(result.selected)} UTXOs:")
    for u in result.selected:
        print(
            f"  - {u.txid[:8]}...:{u.vout}  "
            f"value={u.value_sats} sats  "
            f"input_vbytes={u.input_vbytes}"
        )

    print()
    print(f"Solve time (seconds): {elapsed:.4f}")
    print("Fee (sats):", result.fee_sats)
    print("Change (sats):", result.change_sats)
    print("Tx size (vB):", result.tx_vbytes)
    print("Total input (sats):", result.total_input_sats)
    print("Target (sats):", params.target_sats)


if __name__ == "__main__":
    main()
