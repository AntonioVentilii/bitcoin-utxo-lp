from __future__ import annotations

from typing import TypedDict

from kybra import (
    StableBTreeMap,
    Vec,
    ic,
    init,
    nat32,
    nat64,
    post_upgrade,
    pre_upgrade,
    query,
    update,
    void,
)

from bitcoin_utxo_lp import (
    UTXO,
    SelectionParams,
    SelectionResult,
    SimpleCoinSelectionModel,
    SimpleMILPSolver,
    TxSizing,
)


class StableStorage(TypedDict):
    entries: Vec["Entry"]


class Entry(TypedDict):
    key: str
    value: nat64


class UtxoIn(TypedDict):
    txid: str
    vout: nat32
    value_sats: nat64
    input_vbytes: float


class TxSizingIn(TypedDict):
    base_overhead_vbytes: float
    recipient_output_vbytes: float
    change_output_vbytes: float


class SelectionParamsIn(TypedDict):
    target_sats: nat64
    fee_rate_sat_per_vb: float
    min_change_sats: nat64
    sizing: TxSizingIn


class UtxoOut(TypedDict):
    txid: str
    vout: nat32
    value_sats: nat64
    input_vbytes: float


class SelectionResultOut(TypedDict):
    selected: Vec[UtxoOut]
    change_sats: nat64
    fee_sats: nat64
    tx_vbytes: nat64
    total_input_sats: nat64
    total_output_sats: nat64


class SolveErr(TypedDict):
    message: str


class SolveArgs(TypedDict):
    params: SelectionParamsIn
    utxos: Vec[UtxoIn]


class SolveResult(TypedDict, total=False):
    Ok: SelectionResultOut
    Err: SolveErr


stable_storage = StableBTreeMap[str, Vec[Entry]](
    memory_id=0, max_key_size=100, max_value_size=100
)

entries: dict[str, nat64] = {}


message: str = "Hello!"

solver = SimpleMILPSolver(time_limit_seconds=10)


@init
def init_() -> void:
    ic.print("init_")

    stable_storage.insert("entries", [])


@pre_upgrade
def pre_upgrade_() -> void:
    ic.print("pre_upgrade_")

    stable_storage.insert(
        "entries",
        list(map(lambda item: {"key": item[0], "value": item[1]}, entries.items())),
    )


@post_upgrade
def post_upgrade_() -> void:
    ic.print("post_upgrade_")

    stable_entries = stable_storage.get("entries")

    if stable_entries is not None:
        for stable_entry in stable_entries:
            entries[stable_entry["key"]] = stable_entry["value"]


@update
def set_entry(entry: Entry) -> void:
    entries[entry["key"]] = entry["value"]


@query
def get_entries() -> Vec[Entry]:
    return [{"key": key, "value": entries[key]} for key in entries.keys()]


@query
def get_message() -> str:
    return message


@update
def set_message(new_message: str) -> void:
    global message
    message = new_message


@query
def solve_utxo_selection(args: SolveArgs) -> SolveResult:
    params = args["params"]
    utxos = args["utxos"]

    try:
        utxo_objs = tuple(
            UTXO(
                txid=u["txid"],
                vout=int(u["vout"]),
                value_sats=int(u["value_sats"]),
                input_vbytes=float(u["input_vbytes"]),
            )
            for u in utxos
        )

        sizing_in = params["sizing"]
        sizing = TxSizing(
            base_overhead_vbytes=float(sizing_in["base_overhead_vbytes"]),
            recipient_output_vbytes=float(sizing_in["recipient_output_vbytes"]),
            change_output_vbytes=float(sizing_in["change_output_vbytes"]),
        )

        sel_params = SelectionParams(
            target_sats=int(params["target_sats"]),
            fee_rate_sat_per_vb=float(params["fee_rate_sat_per_vb"]),
            min_change_sats=int(params["min_change_sats"]),
            sizing=sizing,
        )

        model = SimpleCoinSelectionModel(utxos=utxo_objs, params=sel_params)

        res: SelectionResult = solver.solve(model)

        selected_out: Vec[UtxoOut] = [
            {
                "txid": u.txid,
                "vout": u.vout,
                "value_sats": u.value_sats,
                "input_vbytes": float(u.input_vbytes),
            }
            for u in res.selected
        ]

        return {
            "Ok": {
                "selected": selected_out,
                "change_sats": res.change_sats,
                "fee_sats": res.fee_sats,
                "tx_vbytes": res.tx_vbytes,
                "total_input_sats": res.total_input_sats,
                "total_output_sats": res.total_output_sats,
            }
        }

    except Exception as e:
        return {"Err": {"message": str(e)}}
