"""
Inventory valuation under IFRS (IAS 2) and US GAAP (ASC 330).

How on-hand stock is costed
---------------------------
`InventoryItem.quantity` is the number of units on hand.  Each purchase is stored as a
`StockLot` (date, qty, unit cost).  The cost-flow method decides WHICH lots the on-hand
units come from:

  FIFO : oldest units are sold first      -> on-hand units come from the NEWEST lots
  LIFO : newest units are sold first      -> on-hand units come from the OLDEST lots (US GAAP only)
  WAC  : every unit carries the average cost of all lots

If lots do not cover the on-hand quantity, the uncovered units are costed at
`InventoryItem.cost_price` and flagged as "estimated".

Where IFRS and US GAAP differ (the part this module implements)
---------------------------------------------------------------
                      IFRS (IAS 2)                         US GAAP (ASC 330)
 Allowed methods      FIFO, Weighted average               FIFO, LIFO, Weighted average
 LIFO                 Prohibited                           Allowed
 Measurement          Lower of cost and NRV                FIFO / WAC : lower of cost and NRV
                                                           LIFO       : lower of cost and MARKET
                                                                        (market = middle value of replacement cost,
                                                                         NRV ceiling, NRV minus normal profit floor)
 Write-down reversal  REQUIRED if NRV recovers (up to       NOT allowed - a write-down creates a new
                      original cost)                        cost basis

NRV = selling_price - selling_cost.   Replacement cost is approximated by `cost_price`
(the item's current cost); normal profit margin is approximated by selling_price - cost_price.
"""
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal('0')
CENT = Decimal('0.01')

METHOD_LABELS = {'FIFO': 'FIFO', 'LIFO': 'LIFO', 'WAC': 'Weighted Average'}


def q(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


def allowed_methods(company):
    """Methods the company's standard permits."""
    return ['FIFO', 'WAC'] if company.is_ifrs else ['FIFO', 'LIFO', 'WAC']


def effective_method(company):
    """The method actually used.  If the stored method is not permitted under the standard
    (e.g. company was switched from US GAAP to IFRS while on LIFO) fall back to FIFO."""
    return company.inventory_method if company.inventory_method in allowed_methods(company) else 'FIFO'


def _cost_total(item, method):
    """Returns (total_cost, estimated_flag) of the on-hand units for the given cost-flow method."""
    qty = item.quantity
    if qty <= 0:
        return ZERO, False
    lots = list(item.lots.all())

    if method == 'WAC':
        lot_qty = sum(l.quantity for l in lots)
        if lot_qty > 0:
            avg = sum(l.quantity * l.unit_cost for l in lots) / Decimal(lot_qty)
            return q(avg * qty), lot_qty < qty
        return q(item.cost_price * qty), True

    ordered = sorted(lots, key=lambda l: (l.date, l.id), reverse=(method == 'FIFO'))
    remaining, total = qty, ZERO
    for lot in ordered:
        take = min(remaining, lot.quantity)
        total += take * lot.unit_cost
        remaining -= take
        if remaining == 0:
            break
    estimated = remaining > 0
    if estimated:
        total += remaining * item.cost_price      # units with no purchase layer
    return q(total), estimated


def _median(a, b, c):
    return sorted([a, b, c])[1]


def value_item(item, company):
    """Full valuation of one item under the company's standard + method."""
    method = effective_method(company)
    qty = item.quantity
    cost_total, estimated = _cost_total(item, method)
    cost_unit = (cost_total / qty) if qty else ZERO

    nrv_unit = max(ZERO, item.selling_price - item.selling_cost)
    basis = 'Cost'
    market_unit = None

    if not company.is_ifrs and method == 'LIFO':
        # ASC 330-10-35: lower of cost or market
        replacement = item.cost_price
        floor = max(ZERO, nrv_unit - max(ZERO, item.selling_price - item.cost_price))
        market_unit = _median(replacement, nrv_unit, floor)
        limit_unit, limit_name = market_unit, 'Market'
    else:
        limit_unit, limit_name = nrv_unit, 'NRV'

    computed_wd = q(max(ZERO, cost_total - limit_unit * qty)) if qty else ZERO
    if computed_wd > ZERO:
        basis = limit_name

    recorded = item.recorded_writedown or ZERO
    if company.is_ifrs:
        writedown = computed_wd                                   # recovers automatically = reversal
        delta = writedown - recorded
        new_recorded = writedown
        if writedown < recorded:
            basis = 'Cost (write-down reversed)'
    else:
        writedown = min(cost_total, max(computed_wd, recorded))   # never reversed
        delta = max(ZERO, writedown - recorded)
        new_recorded = max(recorded, writedown)
        if writedown > computed_wd and writedown > ZERO:
            basis = 'Prior write-down (no reversal)'

    return {
        'item': item, 'qty': qty, 'method': method,
        'cost_unit': q(cost_unit), 'cost_total': cost_total,
        'nrv_unit': q(nrv_unit), 'market_unit': q(market_unit) if market_unit is not None else None,
        'writedown': q(writedown), 'carrying_total': q(cost_total - writedown),
        'basis': basis, 'estimated': estimated,
        'delta': q(delta), 'new_recorded': q(new_recorded),
    }


def value_inventory(company):
    """Valuation of every item.  Returns dict with rows and totals."""
    from .models import InventoryItem
    items = InventoryItem.objects.filter(company=company).prefetch_related('lots')
    rows = [value_item(i, company) for i in items]
    return {
        'rows': rows,
        'method': effective_method(company),
        'total_cost': sum((r['cost_total'] for r in rows), ZERO),
        'total_writedown': sum((r['writedown'] for r in rows), ZERO),
        'total_carrying': sum((r['carrying_total'] for r in rows), ZERO),
        'net_to_post': sum((r['delta'] for r in rows), ZERO),
    }
