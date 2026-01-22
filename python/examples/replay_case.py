from __future__ import annotations

import argparse
import json
from pathlib import Path

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a saved JSON fixture case and print the solution."
    )
    parser.add_argument(
        "--fixture", default="tests/fixtures/cases_v1.json", help="Path to fixture JSON"
    )
    parser.add_argument("--index", type=int, default=0, help="Case index to replay")
    parser.add_argument(
        "--time-limit", type=int, default=5, help="Solver time limit seconds"
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    cases = payload["cases"]

    if args.index < 0 or args.index >= len(cases):
        raise SystemExit(f"Index out of range: {args.index} (0..{len(cases) - 1})")

    case = cases[args.index]

    sizing = TxSizing(
        base_overhead_vbytes=float(case["base_overhead_vbytes"]),
        recipient_output_vbytes=float(case["recipient_output_vbytes"]),
        change_output_vbytes=float(case["change_output_vbytes"]),
    )

    params = SelectionParams(
        target_sats=int(case["target_sats"]),
        fee_rate_sat_per_vb=float(case["fee_rate_sat_per_vb"]),
        min_change_sats=int(case["min_change_sats"]),
        sizing=sizing,
    )

    utxos = [
        UTXO(
            txid=f"{i:064x}",
            vout=i,
            value_sats=int(u["value_sats"]),
            input_vbytes=float(u["input_vbytes"]),
        )
        for i, u in enumerate(case["utxos"])
    ]

    print(
        f"Case #{args.index} expect={case.get('expect')} "
        f"target={params.target_sats} sats "
        f"feerate={params.fee_rate_sat_per_vb} "
        f"sat/vB min_change={params.min_change_sats}"
    )
    print(f"UTXOs: {len(utxos)} total_value={sum(u.value_sats for u in utxos)} sats")

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver(time_limit_seconds=args.time_limit)

    try:
        res = solver.solve(model)
    except RuntimeError as e:
        print("Solver failed (expected for infeasible cases):", e)
        return

    print("\nSelected UTXOs:")
    for u in res.selected:
        print(
            f"  - {u.txid[:8]}...:{u.vout}  "
            f"value={u.value_sats}  "
            f"in_vB={u.input_vbytes}"
        )

    print("\nResult:")
    print("  tx_vbytes:", res.tx_vbytes)
    print("  fee_sats:", res.fee_sats)
    print("  change_sats:", res.change_sats)
    print("  total_input_sats:", res.total_input_sats)
    print("  target_sats:", params.target_sats)


if __name__ == "__main__":
    main()
