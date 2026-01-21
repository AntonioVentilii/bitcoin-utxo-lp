from bitcoin_utxo_lp import (
    UTXO,
    TxSizing,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
)


def main() -> None:
    utxos = [
        # txid/vout are just identifiers here
        UTXO(txid="a" * 64, vout=0, value_sats=12_000, input_vbytes=68.0),
        UTXO(txid="b" * 64, vout=1, value_sats=25_000, input_vbytes=68.0),
        UTXO(
            txid="c" * 64, vout=2, value_sats=40_000, input_vbytes=58.0
        ),  # e.g. P2TR-ish
        UTXO(
            txid="d" * 64, vout=3, value_sats=9_500, input_vbytes=91.0
        ),  # e.g. P2SH-P2WPKH-ish
        UTXO(txid="e" * 64, vout=4, value_sats=70_000, input_vbytes=68.0),
        UTXO(
            txid="f" * 64, vout=5, value_sats=110_000, input_vbytes=148.0
        ),  # e.g. legacy-ish
    ]

    params = SelectionParams(
        target_sats=300,
        fee_rate_sat_per_vb=1.0,
        min_change_sats=1,
        sizing=TxSizing(
            base_overhead_vbytes=10.0,
            recipient_output_vbytes=31.0,
            change_output_vbytes=31.0,
        ),
    )

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver()

    result = solver.solve(model)

    print("Selected UTXOs:")
    for u in result.selected:
        print(
            f"  - {u.txid[:8]}...:{u.vout}  value={u.value_sats} sats  input_vbytes={u.input_vbytes}"
        )

    print()
    print("Fee (sats):", result.fee_sats)
    print("Change (sats):", result.change_sats)
    print("Tx size (vB):", result.tx_vbytes)
    print("Total input (sats):", result.total_input_sats)
    print("Target (sats):", params.target_sats)


if __name__ == "__main__":
    main()
