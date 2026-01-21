from __future__ import annotations

import json
from pathlib import Path

import pytest

from bitcoin_utxo_lp import (
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
    UTXO,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "cases_v1.json"


def _load_cases() -> list[dict]:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"Missing fixture {FIXTURE_PATH}. Generate it with: "
            "poetry run python tests/utils/gen_cases.py"
        )
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    return payload["cases"]


@pytest.mark.parametrize("case", _load_cases())
def test_saved_cases_v1_invariants(case: dict) -> None:
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

    res = SimpleMILPSolver(time_limit_seconds=5).solve(
        SimpleCoinSelectionModel(utxos=utxos, params=params)
    )

    # Core invariants
    total_in = sum(u.value_sats for u in res.selected)
    assert total_in == params.target_sats + res.fee_sats + res.change_sats
    assert res.change_sats >= params.min_change_sats
    assert res.tx_vbytes > 0
    assert res.fee_sats > 0

    # Selected UTXOs must be subset of candidates
    candidate_keys = {(u.txid, u.vout) for u in utxos}
    selected_keys = {(u.txid, u.vout) for u in res.selected}
    assert selected_keys.issubset(candidate_keys)
