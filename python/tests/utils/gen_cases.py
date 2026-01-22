from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

SCRIPT_DIR = Path(__file__).resolve().parent
TESTS_DIR = SCRIPT_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
DEFAULT_OUT = FIXTURES_DIR / "cases_v1.json"

InputVBytes = Literal["58", "68", "91", "148"]


@dataclass(frozen=True, slots=True)
class UTXOCase:
    value_sats: int
    input_vbytes: str  # stored as string for JSON stability


@dataclass(frozen=True, slots=True)
class CaseV1:
    expect: Literal["feasible", "infeasible"]
    target_sats: int
    fee_rate_sat_per_vb: str
    min_change_sats: int
    base_overhead_vbytes: str
    recipient_output_vbytes: str
    change_output_vbytes: str
    utxos: list[UTXOCase]


def _fee_upper_bound_sat(
    *,
    fee_rate: float,
    base: float,
    recipient_out: float,
    change_out: float,
    utxo_count: int,
    max_input_vbytes: float,
) -> int:
    # Upper bound fee: worst-case assume spending all utxos and large inputs.
    vbytes = base + recipient_out + change_out + (max_input_vbytes * float(utxo_count))
    return int((fee_rate * vbytes) + 0.999999999)  # ceil-ish safe bound


def generate_cases(
    *,
    seed: int = 1337,
    n_cases: int = 30,
    infeasible_ratio: float = 0.2,
) -> list[CaseV1]:
    rnd = random.Random(seed)

    # v1 sizing constants
    base = 10.0
    recipient_out = 31.0
    change_out = 31.0

    input_vbytes_choices: list[InputVBytes] = ["58", "68", "91", "148"]
    max_input_vb = 148.0

    cases: list[CaseV1] = []

    for _case_idx in range(n_cases):
        fee_rate = float(rnd.choice([1, 2, 3, 5, 8, 10]))
        min_change = int(rnd.choice([1, 100, 300, 546]))

        utxo_count = rnd.randint(5, 25)
        target = rnd.randint(2_000, 200_000)

        utxos: list[UTXOCase] = []
        for _ in range(utxo_count):
            vb = rnd.choice(input_vbytes_choices)
            # A few larger UTXOs
            if rnd.random() < 0.8:
                value = rnd.randint(300, 50_000)
            else:
                value = rnd.randint(50_000, 250_000)
            utxos.append(UTXOCase(value_sats=value, input_vbytes=vb))

        total = sum(u.value_sats for u in utxos)
        fee_ub = _fee_upper_bound_sat(
            fee_rate=fee_rate,
            base=base,
            recipient_out=recipient_out,
            change_out=change_out,
            utxo_count=len(utxos),
            max_input_vbytes=max_input_vb,
        )

        required_for_simple = target + min_change + fee_ub

        make_infeasible = rnd.random() < infeasible_ratio

        expect: Literal["feasible", "infeasible"]

        if make_infeasible:
            # Force infeasible by setting target beyond any possible sum, or by
            # setting a too-high min_change relative to total.
            if rnd.random() < 0.5:
                # Target too high
                target = total + rnd.randint(1_000, 50_000)
            else:
                # Make min_change impossible (even if target were met)
                # Increase min_change to exceed any leftover.
                min_change = max(min_change, total + 1)
            expect = "infeasible"
        else:
            # Ensure feasible by topping up with one big UTXO if needed.
            if total < required_for_simple:
                deficit = required_for_simple - total
                utxos.append(
                    UTXOCase(
                        value_sats=deficit + rnd.randint(0, 10_000),
                        input_vbytes="68",
                    )
                )
            expect = "feasible"

        cases.append(
            CaseV1(
                expect=expect,
                target_sats=int(target),
                fee_rate_sat_per_vb=str(fee_rate),
                min_change_sats=int(min_change),
                base_overhead_vbytes=str(base),
                recipient_output_vbytes=str(recipient_out),
                change_output_vbytes=str(change_out),
                utxos=utxos,
            )
        )

    return cases


def save_cases(cases: list[CaseV1], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "cases": [asdict(c) for c in cases]}
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    cases = generate_cases(seed=1337, n_cases=30, infeasible_ratio=0.2)
    save_cases(cases, DEFAULT_OUT)
    print(f"Wrote {len(cases)} cases to: {DEFAULT_OUT}")


if __name__ == "__main__":
    main()
