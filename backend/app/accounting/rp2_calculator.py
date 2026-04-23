from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict, Iterable
from collections import defaultdict


def _import_rp2() -> None:
    """
    Import rp2.

    This project sometimes vendors rp2 under backend/repos/rp2/src.
    We try site-packages first, then fall back to the vendored copy.
    """

    try:
        import rp2  # noqa: F401
        return
    except Exception:
        pass

    import sys

    vendored = Path(__file__).resolve().parents[2] / "repos" / "rp2" / "src"
    if vendored.exists():
        sys.path.insert(0, str(vendored))

    import rp2  # noqa: F401  # pylint: disable=unused-import, import-error


_import_rp2()


@dataclass(frozen=True)
class RP2RunResult:
    total_realized_pnl_usd: float
    realized_pnl_by_asset: dict[str, float]
    taxable_events_count: int
    internal_transfer_count: int
    total_gas_fees_usd: float


def _iter_taxable_transactions(computed_data: Any) -> Iterable[Any]:
    # computed_data is rp2.computed_data.ComputedData
    for entry in computed_data.in_transaction_set:
        if entry.is_taxable():
            yield entry
    for entry in computed_data.out_transaction_set:
        if entry.is_taxable():
            yield entry
    for entry in computed_data.intra_transaction_set:
        if entry.is_taxable():
            yield entry


def compute_pnl_with_rp2(ini_path: str, ods_path: str, method: str | None = None) -> RP2RunResult:
    """
    Compute PnL by delegating accounting logic to rp2.

    It parses the same ODS input that the rp2 CLI consumes and returns a
    simplified summary compatible with this project's existing API shape.
    """

    from importlib import import_module

    from prezzemolo.avl_tree import AVLTree

    from rp2.accounting_engine import AccountingEngine
    from rp2.configuration import Configuration, MIN_DATE
    from rp2.ods_parser import open_ods, parse_ods
    from rp2.tax_engine import compute_tax
    from rp2.plugin.country.us import US

    country = US()
    # In real-world datasets it's common to have missing deposits / partial histories which can
    # temporarily make balances go negative. We allow it to avoid hard failures in the API.
    configuration = Configuration(configuration_path=ini_path, country=country, allow_negative_balances=True)

    # Resolve accounting method(s) like rp2_main does.
    years_2_accounting_method_names = configuration.years_2_accounting_method_names
    if method:
        years_2_accounting_method_names = {MIN_DATE.year: method}
    elif not years_2_accounting_method_names:
        years_2_accounting_method_names = {MIN_DATE.year: country.get_default_accounting_method()}

    years_2_accounting_methods: AVLTree[int, Any] = AVLTree()
    for year, accounting_method_name in years_2_accounting_method_names.items():
        accounting_method_module = import_module(f"rp2.plugin.accounting_method.{accounting_method_name}")
        accounting_method = accounting_method_module.AccountingMethod()
        years_2_accounting_methods.insert_node(int(year), accounting_method)

    accounting_engine = AccountingEngine(years_2_methods=years_2_accounting_methods)

    asset_to_pnl: DefaultDict[str, float] = defaultdict(float)
    taxable_events_count = 0
    total_gas_fees_usd = 0.0

    input_file_handle = open_ods(configuration=configuration, input_file_path=ods_path)

    for asset in sorted(configuration.assets):
        input_data = parse_ods(configuration=configuration, asset=asset, input_file_handle=input_file_handle)
        computed_data = compute_tax(configuration=configuration, accounting_engine=accounting_engine, input_data=input_data)

        # Aggregate realized gain/loss for this asset (sum of all years and transaction types).
        asset_pnl = 0.0
        for ygl in computed_data.yearly_gain_loss_list:
            # ygl.fiat_gain_loss is RP2Decimal
            asset_pnl += float(ygl.fiat_gain_loss)
        asset_to_pnl[asset] += asset_pnl

        # Count taxable events consistently with rp2 rules.
        taxable_events_count += sum(1 for _ in _iter_taxable_transactions(computed_data))

        # Gas / transfer fees are treated by rp2 as taxable intra events (fees).
        # We expose them as a convenience metric.
        for intra in computed_data.intra_transaction_set:
            if intra.is_taxable():
                total_gas_fees_usd += float(intra.fiat_fee)

    return RP2RunResult(
        total_realized_pnl_usd=float(sum(asset_to_pnl.values())),
        realized_pnl_by_asset=dict(asset_to_pnl),
        taxable_events_count=int(taxable_events_count),
        internal_transfer_count=0,  # rp2 doesn't track "matched internal transfers" the same way as our heuristic
        total_gas_fees_usd=float(total_gas_fees_usd),
    )

