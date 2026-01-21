from __future__ import annotations

from dataclasses import dataclass

from .model import SimpleCoinSelectionModel
from .types import UTXO, SelectionResult


@dataclass(frozen=True, slots=True)
class SimpleMILPSolver:
    """
    MILP solver for the SimpleCoinSelectionModel using PuLP.

    Notes:
      - This model ALWAYS creates change and requires change >= min_change_sats.
      - If no feasible solution exists under that policy, it will fail (by design).
    """

    time_limit_seconds: int | None = None

    def solve(self, model: SimpleCoinSelectionModel) -> SelectionResult:
        try:
            import pulp
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "PuLP is required for the MILP solver. Install with: pip install pulp"
            ) from e

        prob, x_vars, change_var, _fee_expr, _vbytes_expr = model.build()

        # Pick a solver.
        # CBC is bundled with many PuLP installs; this is the usual default.
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=self.time_limit_seconds)
        status = prob.solve(solver)

        if pulp.LpStatus[status] != "Optimal":
            raise RuntimeError(
                f"No optimal solution found. Status: {pulp.LpStatus[status]}"
            )

        selected: list[UTXO] = []
        for utxo, x in zip(model.utxos, x_vars):
            xv = x.value()
            if xv is None:
                continue
            if xv > 0.5:
                selected.append(utxo)

        change_val = change_var.value()
        if change_val is None:
            raise RuntimeError("Solver returned no change value")

        # Recompute fee/vbytes in a deterministic integer way
        fee_sats, tx_vbytes = model.evaluate_fee_and_vbytes(selected)

        # Sanity: compute change from balance with integer fee/vbytes
        total_in = sum(u.value_sats for u in selected)
        target = model.params.target_sats
        change_sats = total_in - target - fee_sats

        # Enforce policy sanity (since we recompute fee with ceil)
        if change_sats < model.params.min_change_sats:
            raise RuntimeError(
                "Solution violates min_change after integer fee rounding. "
                "Try slightly higher UTXO sum or adjust sizing/feerate rounding."
            )

        return SelectionResult(
            selected=tuple(selected),
            change_sats=int(change_sats),
            fee_sats=int(fee_sats),
            tx_vbytes=int(tx_vbytes),
        )
