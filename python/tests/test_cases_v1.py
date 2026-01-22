from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

import pytest

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "cases_v1.json"


class CaseUTXO(TypedDict):
    value_sats: int
    input_vbytes: float


class CaseV1(TypedDict):
    base_overhead_vbytes: float
    recipient_output_vbytes: float
    change_output_vbytes: float
    target_sats: int
    fee_rate_sat_per_vb: float
    min_change_sats: int
    utxos: list[CaseUTXO]


class CasesPayloadV1(TypedDict):
    version: int
    cases: list[CaseV1]


def _load_cases() -> list[CaseV1]:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"Missing fixture {FIXTURE_PATH}. Generate it with: "
            "poetry run python tests/utils/gen_cases.py"
        )
    payload = cast(CasesPayloadV1, json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    assert payload["version"] == 1
    return payload["cases"]


@pytest.mark.parametrize("case", _load_cases())
def test_saved_cases_v1_invariants(case: CaseV1) -> None:
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

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver(time_limit_seconds=5)

    if case.get("expect") == "infeasible":
        with pytest.raises(RuntimeError):
            solver.solve(model)
        return

    res = solver.solve(model)

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
