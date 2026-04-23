from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import pandas as pd

from app.accounting.pricing import PriceService

@dataclass
class Lot:
    quantity: float
    unit_cost: float
    timestamp: int
    tx_id: int | None = None
    external_id: str | None = None

@dataclass
class TaxRules:
    treat_airdrop_as_income: bool = True
    treat_staking_as_income: bool = True
    treat_fork_as_income: bool = False  # Most jurisdictions: fork = zero cost basis
    treat_lp_add_as_trade: bool = False # If false, it's just a non-taxable move
    treat_gas_as_expense: bool = True
    apply_wash_sale_rule: bool = False # For US (future)
    cost_basis_method: str = "FIFO" # FIFO, LIFO, HIFO
    deduct_fees_from_proceeds: bool = True

def calculate_pnl(
    df: pd.DataFrame, 
    matches: list[dict[str, Any]], 
    price_service: PriceService,
    rules: TaxRules | None = None
) -> dict[str, Any]:
    if rules is None:
        rules = TaxRules()
    
    # 1. Собираем все индексы внутренних переводов (и отправку, и получение)
    internal_indices = set()
    for m in matches:
        internal_indices.add(int(m["transfer_index"]))
        internal_indices.add(int(m["receive_index"]))

    inventory: dict[str, deque[Lot]] = defaultdict(deque)
    realized_pnl_by_asset: dict[str, float] = defaultdict(float)
    lot_matches = []
    
    total_gas_fees_usd = 0.0
    taxable_events_count = 0
    internal_transfers_count = 0

    # Сортируем строго по времени
    df_sorted = df.sort_values("timestamp").copy()

    for tx_idx, tx in df_sorted.iterrows():
        tx_type = str(tx["type"]).upper()
        ts_raw = tx["timestamp"]
        timestamp = int(ts_raw.timestamp()) if hasattr(ts_raw, 'timestamp') else int(ts_raw)
        dt_ts = ts_raw if hasattr(ts_raw, 'timestamp') else datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        asset = str(tx["asset"])
        amount = float(tx.get("amount", 0.0) or 0.0)
        tx_id = tx.get("id")
        external_id = tx.get("external_id")

        # --- CUSTOM TAG OVERRIDE ---
        # Пользовательская метка переопределяет тип транзакции для расчёта налога.
        # Это ключевая фича для корректности: алгоритм не всегда угадывает.
        custom_tag = str(tx.get("custom_tag", "") or "").lower().strip()
        _TAG_TO_TYPE = {
            "gift":     "AIRDROP",       # Подарок → income по рыночной цене
            "donation": "AIRDROP",       # Пожертвование → аналогично подарку
            "personal": "TRANSFER",      # Личный перевод → не налогооблагаемый
            "lost":     "TRANSFER",      # Потеря → списание без прибыли
            "stolen":   "TRANSFER",      # Кража → аналогично потере
            "payment":  "INCOME",        # Оплата за работу → income
            "salary":   "INCOME",        # Зарплата → income
            "fork":     "FORK",          # Хардфорк
            "mining":   "MINING_REWARD", # Майнинг
            "ignore":   "_IGNORE",       # Полностью игнорировать транзакцию
        }
        if custom_tag in _TAG_TO_TYPE:
            override = _TAG_TO_TYPE[custom_tag]
            if override == "_IGNORE":
                continue  # Пропускаем полностью
            tx_type = override
        
        # Получаем параметры комиссии
        fee_amount = float(tx.get("fee", 0.0) or 0.0)
        fee_asset = str(tx.get("fee_asset", asset)) 
        
        # Считаем стоимость комиссии один раз для этой строки
        fee_usd = 0.0
        if fee_amount > 0:
            fee_token_price = price_service.get_historical_price_usd(fee_asset, timestamp)
            fee_usd = fee_amount * fee_token_price

        # --- ГЛАВНАЯ ЛОГИКА ---

        # Случай А: Это ВНУТРЕННИЙ ПЕРЕВОД (Match)
        if int(tx_idx) in internal_indices:
            if tx_type == "TRANSFER":
                total_gas_fees_usd += fee_usd
                realized_pnl_by_asset["GAS_EXPENSE"] -= fee_usd
                internal_transfers_count += 1
            # Добавляем в инвентарь при получении, если это внутренний перевод
            if tx_type == "RECEIVE":
                # Внутренний перевод не меняет себестоимость (упрощение)
                # В идеале нужно переносить Lot из исходящего кошелька, но здесь мы упрощаем
                market_price = _resolve_market_price(tx, asset, timestamp, price_service)
                inventory[asset].append(Lot(
                    quantity=amount, 
                    unit_cost=market_price, 
                    timestamp=timestamp,
                    tx_id=tx_id,
                    external_id=external_id
                ))
            continue

        total_gas_fees_usd += fee_usd

        # Случай Б: ПОКУПКА
        if tx_type in ["BUY", "RECEIVE"]:
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            total_cost = (amount * market_price) + fee_usd
            unit_cost = total_cost / amount if amount > 0 else 0.0
            
            inventory[asset].append(Lot(
                quantity=amount, 
                unit_cost=unit_cost, 
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id
            ))

        # Случай В: ПРОДАЖА
        elif tx_type == "SELL":
            taxable_events_count += 1
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            total_proceeds = (amount * market_price) - fee_usd
            
            try:
                cost_basis, consumed = _consume_lots(rules.cost_basis_method, inventory[asset], amount)
                realized_pnl_by_asset[asset] += (total_proceeds - cost_basis)
                
                # Добавляем детали матчинга для Audit Trail
                for c in consumed:
                    lot_matches.append({
                        "asset": asset,
                        "amount": c["amount"],
                        "buy_price": c["unit_cost"],
                        "sell_price": market_price,
                        "cost_basis": c["cost_basis"],
                        "proceeds": (c["amount"] / amount) * total_proceeds if amount > 0 else 0,
                        "gain_loss": ((c["amount"] / amount) * total_proceeds) - c["cost_basis"] if amount > 0 else 0,
                        "buy_timestamp": datetime.fromtimestamp(c["buy_timestamp"], tz=timezone.utc),
                        "sell_timestamp": dt_ts,
                        "sell_tx_id": tx_id,
                        "sell_tx_external_id": external_id,
                        "buy_tx_id": c["buy_tx_id"],
                        "buy_tx_external_id": c["buy_external_id"],
                    })
            except ValueError as e:
                print(f"⚠️ Ошибка FIFO для {asset} (индекс {tx_idx}): {e}")

        # Случай Г: ОБМЕН (SWAP)
        elif tx_type in ["SWAP", "TRADE"]:
            taxable_events_count += 1
            a_out, am_out = str(tx["asset_out"]), float(tx["amount_out"])
            a_in, am_in = str(tx["asset_in"]), float(tx["amount_in"])

            p_out = price_service.get_historical_price_usd(a_out, timestamp)
            proceeds = (am_out * p_out) - fee_usd
            
            cost_basis_out, consumed = _consume_lots(rules.cost_basis_method, inventory[a_out], am_out)
            realized_pnl_by_asset[a_out] += (proceeds - cost_basis_out)
            
            # Audit matches for the sold part of the swap
            for c in consumed:
                lot_matches.append({
                    "asset": a_out,
                    "amount": c["amount"],
                    "buy_price": c["unit_cost"],
                    "sell_price": p_out,
                    "cost_basis": c["cost_basis"],
                    "proceeds": (c["amount"] / am_out) * proceeds if am_out > 0 else 0,
                    "gain_loss": ((c["amount"] / am_out) * proceeds) - c["cost_basis"] if am_out > 0 else 0,
                    "buy_timestamp": datetime.fromtimestamp(c["buy_timestamp"], tz=timezone.utc),
                    "sell_timestamp": dt_ts,
                    "sell_tx_id": tx_id,
                    "sell_tx_external_id": external_id,
                    "buy_tx_id": c["buy_tx_id"],
                    "buy_tx_external_id": c["buy_external_id"],
                })
            
            # Входящий актив получает стоимость на основе проданного
            unit_cost_in = proceeds / am_in if am_in > 0 else 0.0
            inventory[a_in].append(Lot(
                quantity=am_in, 
                unit_cost=unit_cost_in, 
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id
            ))

        # Случай Д: Доходные события (STAKING_REWARD, FARMING_REWARD, AIRDROP)
        elif tx_type in ["STAKING_REWARD", "FARMING_REWARD", "AIRDROP", "INCOME"]:
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            
            is_airdrop = tx_type == "AIRDROP"
            is_staking = tx_type in ["STAKING_REWARD", "FARMING_REWARD"]
            
            record_income = True
            if is_airdrop and not rules.treat_airdrop_as_income:
                record_income = False
            if is_staking and not rules.treat_staking_as_income:
                record_income = False
                
            if record_income:
                income_usd = amount * market_price
                realized_pnl_by_asset["INCOME"] += income_usd
            
            inventory[asset].append(Lot(
                quantity=amount, 
                unit_cost=market_price if record_income else 0.0, 
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id
            ))

        # Случай Д2: FORK — новые монеты от хардфорка (BCH из BTC, и т.д.)
        elif tx_type == "FORK":
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)

            if rules.treat_fork_as_income:
                # Некоторые юрисдикции: fork = income по рыночной цене
                income_usd = amount * market_price
                realized_pnl_by_asset["INCOME"] += income_usd
                cost = market_price
            else:
                # Большинство юрисдикций (US IRS Rev. Ruling 2019-24): fork = $0 cost basis
                # Налог только при продаже, по полной цене продажи
                cost = 0.0

            inventory[asset].append(Lot(
                quantity=amount,
                unit_cost=cost,
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id,
            ))

        # Случай Д3: BRIDGE — перевод между сетями, не налогооблагаемый
        elif tx_type == "BRIDGE":
            # Bridge = неналогооблагаемый перенос. Сохраняем оригинальную себестоимость.
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            inventory[asset].append(Lot(
                quantity=amount,
                unit_cost=market_price,
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id,
            ))
            total_gas_fees_usd += fee_usd

        # Случай Е: DeFi - LP ADD
        elif tx_type == "DEFI_LP_ADD":
            tokens_in = tx.get("defi_tokens_in", {}) 
            tokens_out = tx.get("defi_tokens_out", {}) 
            
            if tokens_in and tokens_out:
                total_cb = 0.0
                total_market_value = 0.0
                
                for a_in, am_in in tokens_in.items():
                    cb, _ = _consume_lots(rules.cost_basis_method, inventory[a_in], am_in)
                    total_cb += cb
                    total_market_value += (am_in * price_service.get_historical_price_usd(a_in, timestamp))
                
                if rules.treat_lp_add_as_trade:
                    # Treat as a sale of component tokens
                    realized_pnl_by_asset["DEFI"] += (total_market_value - total_cb)
                    taxable_events_count += 1
                
                for lp_asset, lp_amount in tokens_out.items():
                    # If trade, unit cost is market value. If move, unit cost is carry-over cost basis.
                    unit_cost = (total_market_value if rules.treat_lp_add_as_trade else total_cb) / lp_amount if lp_amount > 0 else 0.0
                    inventory[lp_asset].append(Lot(
                        quantity=lp_amount, 
                        unit_cost=unit_cost, 
                        timestamp=timestamp,
                        tx_id=tx_id,
                        external_id=external_id
                    ))

        # Случай З: NFT (MINT/SALE)
        elif tx_type == "NFT_MINT":
            # Usually costs gas + mint price
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            inventory[asset].append(Lot(
                quantity=amount, 
                unit_cost=market_price + (fee_usd / amount if amount > 0 else 0), 
                timestamp=timestamp,
                tx_id=tx_id,
                external_id=external_id
            ))

        # Случай И: Margin / Futures / Liquidations
        elif tx_type == "LIQUIDATION":
            # Collateral is lost
            market_price = _resolve_market_price(tx, asset, timestamp, price_service)
            try:
                cb, _ = _consume_lots(rules.cost_basis_method, inventory[asset], amount)
                # This is a capital loss (total proceeds = 0 for the user)
                realized_pnl_by_asset[asset] -= cb
                taxable_events_count += 1
            except ValueError:
                pass # Already empty?

        elif tx_type == "FUTURES_PNL":
            # Realized PnL from derivatives (often in USDC/USDT)
            # 'amount' here is the profit (if >0) or loss (if <0)
            realized_pnl_by_asset["FUTURES"] += amount
            taxable_events_count += 1

        # Случай Ж: DeFi - LP REMOVE
        elif tx_type == "DEFI_LP_REMOVE":
            tokens_in = tx.get("defi_tokens_in", {}) # LP Token burned
            tokens_out = tx.get("defi_tokens_out", {}) # Assets received
            
            if tokens_in and tokens_out:
                total_proceeds = 0.0
                for a_out, am_out in tokens_out.items():
                    p = am_out * price_service.get_historical_price_usd(a_out, timestamp)
                    total_proceeds += p
                    
                    # Полученные активы заходят в инвентарь по рыночной цене
                    inventory[a_out].append(Lot(
                        quantity=am_out, 
                        unit_cost=p / am_out if am_out > 0 else 0.0, 
                        timestamp=timestamp,
                        tx_id=tx_id,
                        external_id=external_id
                    ))
                
                for lp_asset, lp_amount in tokens_in.items():
                    cb, consumed = _consume_lots(rules.cost_basis_method, inventory[lp_asset], lp_amount)
                    realized_pnl_by_asset[lp_asset] += (total_proceeds - cb)
                    taxable_events_count += 1

    return {
        "total_realized_pnl_usd": float(sum(realized_pnl_by_asset.values())),
        "realized_pnl_by_asset": dict(realized_pnl_by_asset),
        "taxable_events_count": taxable_events_count,
        "internal_transfer_count": internal_transfers_count,
        "total_gas_fees_usd": total_gas_fees_usd,
        "lot_matches": lot_matches,
    }

def _resolve_market_price(tx: pd.Series, asset: str, timestamp: int, price_service: PriceService) -> float:
    """Определяет рыночную цену: сначала из CSV, затем из API."""
    # Если в CSV есть цена и она адекватна (не 1.0 для дорогих активов)
    csv_price = float(tx.get("price", 0.0) or 0.0)
    if csv_price > 0:
        if not (csv_price == 1.0 and asset.upper() not in ["USD", "USDT", "USDC", "DAI"]):
            return csv_price
            
    # Иначе идем в Binance API
    return price_service.get_historical_price_usd(asset, timestamp)

def _consume_lots(method: str, lots: deque[Lot], quantity_to_sell: float) -> tuple[float, list[dict[str, Any]]]:
    """Route to the correct cost basis method."""
    method_upper = method.upper()
    if method_upper == "LIFO":
        return _consume_lifo(lots, quantity_to_sell)
    elif method_upper == "HIFO":
        return _consume_hifo(lots, quantity_to_sell)
    else:
        return _consume_fifo(lots, quantity_to_sell)


def _consume_fifo(lots: deque[Lot], quantity_to_sell: float) -> tuple[float, list[dict[str, Any]]]:
    """First-In, First-Out: sell oldest lots first."""
    remaining = quantity_to_sell
    total_cost_basis = 0.0
    consumed_lots = []
    
    while remaining > 1e-12 and lots:
        lot = lots[0]
        consumed = min(lot.quantity, remaining)
        
        lot_cost = consumed * lot.unit_cost
        total_cost_basis += lot_cost
        
        consumed_lots.append({
            "amount": consumed,
            "unit_cost": lot.unit_cost,
            "cost_basis": lot_cost,
            "buy_timestamp": lot.timestamp,
            "buy_tx_id": lot.tx_id,
            "buy_external_id": lot.external_id,
        })
        
        lot.quantity -= consumed
        remaining -= consumed
        if lot.quantity <= 1e-12:
            lots.popleft()
            
    if remaining > 1e-12:
        raise ValueError(f"Недостаточно монет: нужно еще {remaining:.8f}")
    return total_cost_basis, consumed_lots


def _consume_lifo(lots: deque[Lot], quantity_to_sell: float) -> tuple[float, list[dict[str, Any]]]:
    """Last-In, First-Out: sell newest lots first (lower tax on rising markets)."""
    remaining = quantity_to_sell
    total_cost_basis = 0.0
    consumed_lots = []
    
    while remaining > 1e-12 and lots:
        lot = lots[-1]  # берём с конца — последний купленный
        consumed = min(lot.quantity, remaining)
        
        lot_cost = consumed * lot.unit_cost
        total_cost_basis += lot_cost
        
        consumed_lots.append({
            "amount": consumed,
            "unit_cost": lot.unit_cost,
            "cost_basis": lot_cost,
            "buy_timestamp": lot.timestamp,
            "buy_tx_id": lot.tx_id,
            "buy_external_id": lot.external_id,
        })
        
        lot.quantity -= consumed
        remaining -= consumed
        if lot.quantity <= 1e-12:
            lots.pop()  # удаляем с конца
            
    if remaining > 1e-12:
        raise ValueError(f"Недостаточно монет: нужно еще {remaining:.8f}")
    return total_cost_basis, consumed_lots


def _consume_hifo(lots: deque[Lot], quantity_to_sell: float) -> tuple[float, list[dict[str, Any]]]:
    """Highest-In, First-Out: sell most expensive lots first (maximum tax savings)."""
    remaining = quantity_to_sell
    total_cost_basis = 0.0
    consumed_lots = []
    
    while remaining > 1e-12 and lots:
        # Находим лот с максимальной ценой покупки
        max_idx = 0
        for i in range(1, len(lots)):
            if lots[i].unit_cost > lots[max_idx].unit_cost:
                max_idx = i
        
        lot = lots[max_idx]
        consumed = min(lot.quantity, remaining)
        
        lot_cost = consumed * lot.unit_cost
        total_cost_basis += lot_cost
        
        consumed_lots.append({
            "amount": consumed,
            "unit_cost": lot.unit_cost,
            "cost_basis": lot_cost,
            "buy_timestamp": lot.timestamp,
            "buy_tx_id": lot.tx_id,
            "buy_external_id": lot.external_id,
        })
        
        lot.quantity -= consumed
        remaining -= consumed
        if lot.quantity <= 1e-12:
            del lots[max_idx]
            
    if remaining > 1e-12:
        raise ValueError(f"Недостаточно монет: нужно еще {remaining:.8f}")
    return total_cost_basis, consumed_lots