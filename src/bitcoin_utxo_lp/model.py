from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import pulp

from .types import UTXO, SelectionParams


@dataclass(frozen=True, slots=True)
class SimpleCoinSelectionModel:
    """
    Simple model:
      - always includes a change output
      - enforces change >= min_change_sats
      - minimises fee (equivalently minimises total input vbytes)
    """

    utxos: Sequence[UTXO]
    params: SelectionParams

    def _ceil_int(self, x: float) -> int:
        # vbytes should be treated as an integer for fee calculation
        return math.ceil(x)

    def fixed_vbytes(self) -> float:
        p = self.params
        return (
            p.sizing.base_overhead_vbytes
            + p.sizing.recipient_output_vbytes
            + p.sizing.change_output_vbytes
        )

    def build(
        self,
    ) -> tuple[
        pulp.LpProblem,
        list[pulp.LpVariable],
        pulp.LpVariable,
        pulp.LpAffineExpression,
        pulp.LpAffineExpression,
    ]:
        """
        Builds and returns:
          (problem, x_vars, change_var, fee_expr, vbytes_expr)
        where x_vars is a list aligned with self.utxos.
        """

        p = self.params

        if p.target_sats < 0:
            raise ValueError("target_sats must be >= 0")
        if p.min_change_sats < 0:
            raise ValueError("min_change_sats must be >= 0")
        if p.fee_rate_sat_per_vb <= 0:
            raise ValueError("fee_rate_sat_per_vb must be > 0")
        if not self.utxos:
            raise ValueError("No UTXOs provided")

        # Problem
        prob = pulp.LpProblem("coin_selection_simple", pulp.LpMinimize)

        # Decision variables: x_i in {0,1}
        x = [
            pulp.LpVariable(f"x_{i}", lowBound=0, upBound=1, cat=pulp.LpBinary)
            for i in range(len(self.utxos))
        ]

        # Change (integer sats)
        change = pulp.LpVariable("change_sats", lowBound=0, cat=pulp.LpInteger)

        # vbytes = fixed + sum(s_i * x_i)
        fixed_vb = self.fixed_vbytes()
        input_vb_expr = pulp.lpSum(
            [u.input_vbytes * x_i for u, x_i in zip(self.utxos, x)]
        )
        vbytes_expr = fixed_vb + input_vb_expr

        # Fee = feerate * vbytes
        fee_expr = (p.fee_rate_sat_per_vb) * vbytes_expr

        # Balance equality:
        # sum(v_i * x_i) = target + change + fee
        total_in_expr = pulp.lpSum(
            [u.value_sats * x_i for u, x_i in zip(self.utxos, x)]
        )
        prob += (total_in_expr == p.target_sats + change + fee_expr), "balance"

        # Enforce dust / min change (because change output always exists)
        prob += (change >= p.min_change_sats), "min_change"

        # Objective: minimise fee
        # (same as minimise sum(input vbytes) since others are constant)
        prob += fee_expr, "minimise_fee"

        return prob, x, change, fee_expr, vbytes_expr

    def evaluate_fee_and_vbytes(self, selected: Sequence[UTXO]) -> tuple[int, int]:
        """
        Deterministic post-solve computation using integer vbytes (ceil),
        so your library returns consistent, wallet-like figures.
        """
        p = self.params
        vbytes = self.fixed_vbytes() + sum((u.input_vbytes for u in selected), 0.0)
        vbytes_i = self._ceil_int(vbytes)
        fee = math.ceil(float(p.fee_rate_sat_per_vb) * float(vbytes_i))
        return int(fee), int(vbytes_i)
