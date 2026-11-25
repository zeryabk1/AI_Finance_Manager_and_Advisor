# IFRS vs US GAAP in AI Finance Manager

Choose the standard in **Companies -> Edit -> Accounting standard** (and the inventory method right below it).
Everything below switches automatically for that company.

## 1. Inventory valuation  (Inventory -> Valuation)
| | IFRS (IAS 2) | US GAAP (ASC 330) |
|---|---|---|
| Allowed methods | FIFO, Weighted average | FIFO, LIFO, Weighted average |
| LIFO | **Prohibited** (form blocks it) | Allowed |
| Measurement | Lower of cost and NRV | FIFO/Avg: lower of cost and NRV. LIFO: lower of cost and *market* |
| Write-down reversal | **Required** when NRV recovers (up to original cost) | **Not allowed** - write-down is the new cost basis |

* On-hand units are costed from purchase layers (Inventory -> Layers / Receive). New items get an opening layer automatically.
* NRV = selling price - estimated selling cost (new item field). Market (LIFO) = middle of replacement cost, NRV, and NRV minus normal margin.
* "Post adjustment to ledger" books Dr Inventory Write-down / Cr Inventory (IFRS reversals post the opposite way).

## 2. Financial statement presentation
| | IFRS (IAS 1) | US GAAP |
|---|---|---|
| Names | Statement of Financial Position / Statement of Profit or Loss and OCI | Balance Sheet / Income Statement |
| Assets | Non-current first, then current | Current first (liquidity), then non-current |
| Funding side | Equity, non-current liabilities, current liabilities | Liabilities (current, long-term), then stockholders' equity |
| Income statement | Single-step, expenses by nature, finance costs separate, OCI shown | Multi-step by function: gross profit, operating income, other income/expense, net income |

Accounts are sorted into sections from their code and name (e.g. code >= 1500 or "Machinery" = non-current;
"Interest" = finance cost; "Cost of Goods Sold" = COGS) - see `accounting/standards.py` (`classify`).
Both standards read the same ledger, so total assets and net profit are always identical.
