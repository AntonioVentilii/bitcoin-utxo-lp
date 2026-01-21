from __future__ import annotations

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)

# Keep sizes modest so MILP remains quick.
st_input_vbytes = st.sampled_from([58.0, 68.0, 91.0, 148.0])


@st.composite
def st_case(draw):
    n = draw(st.integers(min_value=3, max_value=18))
    utxos = [
        UTXO(
            txid=f"{i:064x}",
            vout=i,
            value_sats=draw(st.integers(min_value=300, max_value=80_000)),
            input_vbytes=draw(st_input_vbytes),
        )
        for i in range(n)
    ]

    sizing = TxSizing(
        base_overhead_vbytes=10.0,
        recipient_output_vbytes=31.0,
        change_output_vbytes=31.0,
    )

    fee_rate = draw(
        st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    min_change = draw(st.integers(min_value=1, max_value=1_000))

    total = sum(u.value_sats for u in utxos)
    # Choose target likely feasible but not guaranteed (Hypothesis will explore both)
    target = draw(st.integers(min_value=1_000, max_value=max(1_000, total)))

    params = SelectionParams(
        target_sats=int(target),
        fee_rate_sat_per_vb=float(fee_rate),
        min_change_sats=int(min_change),
        sizing=sizing,
    )

    return utxos, params


@settings(max_examples=50, deadline=None)
@given(st_case())
def test_property_invariants_or_infeasible(case) -> None:
    utxos, params = case

    model = SimpleCoinSelectionModel(utxos=utxos, params=params)
    solver = SimpleMILPSolver(time_limit_seconds=3)

    try:
        res = solver.solve(model)
    except RuntimeError:
        # Infeasible is acceptable for this simple model.
        return

    total_in = sum(u.value_sats for u in res.selected)
    assert total_in == params.target_sats + res.fee_sats + res.change_sats
    assert res.change_sats >= params.min_change_sats
    assert res.tx_vbytes > 0
    assert res.fee_sats > 0

    # Fee is consistent with tx_vbytes (wallet-style ceil)
    assert res.fee_sats == math.ceil(params.fee_rate_sat_per_vb * res.tx_vbytes)
