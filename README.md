# bitcoin-utxo-lp

A **Bitcoin UTXO coin-selection engine** built around **Linear Programming (LP)** and **Mixed-Integer Linear
Programming (MILP)** models.

This library focuses on **optimal, explainable, and testable** UTXO selection under realistic Bitcoin constraints: fees,
dust, change outputs, and input sizes.

___

## Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Example](#-quick-example)
- [Core Concepts](#-core-concepts)
    - [UTXO](#utxo)
    - [Selection Parameters](#selection-parameters)
- [Optimisation Models](#-optimisation-models)
    - [SimpleCoinSelectionModel](#simplecoinselectionmodel)
    - [Solvers](#solvers)
- [Solution Object](#-solution-object)
- [Testing Philosophy](#-testing-philosophy)
- [Type Checking](#️-type-checking)
- [Safety & Correctness](#-safety--correctness)
- [License](#-license)

---

## ✨ Features

* 🔢 **LP & MILP coin selection models**
* ⚖️ Optimises for:

    * minimal fee cost
    * minimal excess change
    * minimal number of inputs
* 📏 Precise fee modelling using **vbytes**
* 🔄 Deterministic and reproducible solutions
* 🧪 Designed for property-based and scenario testing
* 🧩 Extensible objective functions and constraints

## 📦 Installation

Using **Poetry** (recommended):

```bash
poetry add bitcoin-utxo-lp
```

Or for development:

```bash
git clone https://github.com/<your-org>/bitcoin-utxo-lp.git
cd bitcoin-utxo-lp
poetry install
```

## 🚀 Quick Example

```python
from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
)

utxos = [
    UTXO(
        txid="a" * 64,
        vout=0,
        value_sats=1_000,
        input_vbytes=68.0,
    ),
]

params = SelectionParams(
    target_sats=300,
    fee_rate_sat_per_vb=1.0,
    min_change_sats=1,
)

model = SimpleCoinSelectionModel(utxos, params)
solver = SimpleMILPSolver()

solution = solver.solve(model)

print(solution.selected_utxos)
print(solution.total_fee_sats)
print(solution.change_sats)
```

## 🧠 Core Concepts

### UTXO

A spendable output with an associated **fee footprint**:

```python
UTXO(
    txid: str,
    vout: int,
    value_sats: int,
    input_vbytes: float,
)
```

Fee cost is computed as:

```
input_vbytes × fee_rate_sat_per_vb
```

### Selection Parameters

```python
SelectionParams(
    target_sats: int,
fee_rate_sat_per_vb: float,
min_change_sats: int,
)
```

These parameters fully define the optimisation problem.

## 🧮 Optimisation Models

### SimpleCoinSelectionModel

Encodes the selection problem as a linear or mixed-integer program:

* Binary variable per UTXO (`x_i ∈ {0,1}`)
* Constraints:

    * selected_value − fees ≥ target
    * change ≥ min_change
* Objective:

    * minimise weighted sum of:

        * fees
        * change
        * number of inputs

The model is **solver-agnostic**.

### Solvers

#### SimpleMILPSolver

* Uses integer decision variables
* Guarantees **globally optimal** solutions
* Suitable for wallets, batching, and backtesting

(An LP-relaxed solver can be added later for heuristics.)

## 📤 Solution Object

The solver returns a structured result:

```python
solution.selected_utxos
solution.total_input_sats
solution.total_fee_sats
solution.change_sats
solution.is_optimal
```

This makes it easy to:

* inspect decisions
* debug constraints
* export metrics

## 🧪 Testing Philosophy

The project is designed for **test-first optimisation**.

Recommended test categories:

### Deterministic Scenarios

* single UTXO exact match
* exact target + fee
* forced change creation
* dust rejection

### Edge Cases

* insufficient funds
* fee > UTXO value
* zero-change solutions
* large fee rates

### Property-Based Tests

* monotonicity w.r.t fee rate
* solution validity invariants
* no negative change
* no overspending

## ⚙️ Type Checking

This project is **fully typed** and designed to work with `mypy`.

If you see:

```
Skipping analyzing "pulp": missing library stubs
```

Recommended fix:

```ini
# mypy.ini
[mypy-pulp]
ignore_missing_imports = true
```

This keeps strict typing everywhere else.

## 🔐 Safety & Correctness

This library **does not construct transactions** and **does not sign anything**.

It only solves the **selection problem**.
Transaction construction, signing, and broadcast must be handled separately.

## 📜 License

TBD
