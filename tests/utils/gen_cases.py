from __future__ import annotations
import math
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

SCRIPT_DIR = Path(__file__).resolve().parent
TESTS_DIR = SCRIPT_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
DEFAULT_OUT = FIXTURES_DIR / "cases_v1.json"


InputVBytes = Literal["58", "68", "91", "148"]  # common-ish estimates


@dataclass(frozen=True, slots=True)
class UTXOCase:
    value_sats: int
    input_vbytes: str  # Float-as-string for JSON stability


@dataclass(frozen=True, slots=True)
class CaseV1:
    target_sats: int
    fee_rate_sat_per_vb: str
    min_change_sats: int

    base_overhead_vbytes: str
    recipient_output_vbytes: str
    change_output_vbytes: str

    utxos: list[UTXOCase]


def _d(x: str) -> float:
    return float(x)


def _fee_upper_bound_sat(
    fee_rate: float,
    base: float,
    recipient_out: float,
    change_out: float,
    utxo_count: int,
    max_input_vbytes: float,
) -> int:
    # Upper bound fee: assume you might (worst-case) use all utxos with large inputs.
    vbytes = base + recipient_out + change_out + (max_input_vbytes * float(utxo_count))
    return int(math.ceil(fee_rate * vbytes))


def generate_cases(
    *,
    seed: int = 1337,
    n_cases: int = 30,
) -> list[CaseV1]:
    rnd = random.Random(seed)

    # Reasonable fixed sizing for v1 (you can evolve later)
    base = _d("10")
    recipient_out = _d("31")
    change_out = _d("31")

    # Common-ish input sizes (vB) as strings
    input_vbytes_choices: list[InputVBytes] = [
        "58",
        "68",
        "91",
        "148",
    ]  # P2TR, P2WPKH, P2SH-P2WPKH, P2PKH
    max_input_vb = _d("148")

    cases: list[CaseV1] = []

    for _case_idx in range(n_cases):
        fee_rate = float(rnd.choice([1, 2, 3, 5, 8, 10]))  # sat/vB
        min_change = rnd.choice(
            [1, 100, 300, 546]
        )  # include classic-ish dust-ish values

        utxo_count = rnd.randint(5, 25)

        # Targets: keep within typical small-wallet toy ranges
        target = rnd.randint(2_000, 200_000)

        utxos: list[UTXOCase] = []
        for _ in range(utxo_count):
            vb = rnd.choice(input_vbytes_choices)
            # Heavier tails: some tiny, some medium, some larger
            value = (
                rnd.randint(300, 50_000)
                if rnd.random() < 0.8
                else rnd.randint(50_000, 250_000)
            )
            utxos.append(UTXOCase(value_sats=value, input_vbytes=vb))

        # Ensure feasibility for the *simple* model:
        # sum(inputs) >= target + min_change + fee_upper_bound
        total = sum(u.value_sats for u in utxos)
        fee_ub = _fee_upper_bound_sat(
            fee_rate, base, recipient_out, change_out, len(utxos), max_input_vb
        )
        required = target + min_change + fee_ub

        if total < required:
            # top up with one big utxo to make the case solvable
            deficit = required - total
            utxos.append(
                UTXOCase(
                    value_sats=deficit + rnd.randint(0, 10_000),
                    input_vbytes="68",
                )
            )

        cases.append(
            CaseV1(
                target_sats=target,
                fee_rate_sat_per_vb=str(fee_rate),
                min_change_sats=min_change,
                base_overhead_vbytes=str(base),
                recipient_output_vbytes=str(recipient_out),
                change_output_vbytes=str(change_out),
                utxos=utxos,
            )
        )

    return cases


def save_cases(cases: list[CaseV1], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "cases": [asdict(c) for c in cases],
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    cases = generate_cases(seed=1337, n_cases=30)
    save_cases(cases, DEFAULT_OUT)
    print(f"Wrote {len(cases)} cases to: {DEFAULT_OUT}")


if __name__ == "__main__":
    main()
