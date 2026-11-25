# AI Finance Manager — Final Year Project

A modular Django-based financial management system with double-entry
accounting, inventory, fixed assets, a REST API, and 4 working AI
modules (fraud detection, business stability index, bankruptcy
prediction, cash flow prediction).

## 🚀 Fastest way to start (one command)

**Mac/Linux:**
```bash
cd AI_Finance_Manager
chmod +x setup.sh
./setup.sh
```

**Windows:** double-click `setup.bat` inside the `AI_Finance_Manager`
folder (or run it from a Command Prompt).

Either script will: create a virtual environment, install every
dependency, build the SQLite database, load demo data, train both AI
models, and start the server — then open **http://127.0.0.1:8000/**
and log in with **demo / demo12345**.

If you'd rather run each step yourself (or the script hits an issue
on your system), the manual step-by-step instructions are below.

---

## 🔐 Role-based access control (new)

Each user has one global role (set at registration, or changed later
via Django Admin): **Super Admin**, **Company Owner**, **Accountant**,
or **Employee**. Roles now actually change what you can do:

| Action | Super Admin | Company Owner | Accountant | Employee |
|---|---|---|---|---|
| See every company in the system | Yes | No (only their own + companies they're granted access to) | No | No |
| Create / edit / delete a company | Yes | Yes (their own) | No | No |
| Grant/remove staff access to a company | Yes | Yes (their own) | No | No |
| Add/edit/delete Chart of Accounts | Yes | Yes | Yes | No (view only) |
| Add journal entries | Yes | Yes | Yes | No (view only) |
| Add/edit/delete Budget lines | Yes | Yes | Yes | No (view only) |
| Customers, Suppliers, Sales Invoices, Purchase Bills, Payments, Inventory, Fixed Assets | Yes | Yes | Yes | Yes |
| View Ledger, Trial Balance, P&L, Balance Sheet, AI Reports | Yes | Yes | Yes | Yes (read only) |

**How a Company Owner adds an Accountant/Employee to their company
(updated):** go to **Companies -> Staff** (next to Edit/Delete) on that
company. Fill in the person's name, email, role (Accountant or
Employee), and a password — click **Create & Grant Access**. That's
it: no separate registration step. The staff member then logs in at
the normal login page using just that **email + password**, and lands
directly in the company they were added to.

If the email you enter already belongs to an existing Accountant/
Employee account (e.g. someone you've already set up for a different
company), the form just grants that existing account access to this
company too instead of creating a duplicate — the password field is
ignored in that case.

**Public registration** (`/accounts/register/`) now always creates a
**Company Owner** account — Accountants and Employees no longer
self-register at all; they only ever get an account through the
Companies -> Staff flow above.

**Super Admin accounts** still can't be created via the public
registration form (by design). To make one: run `createsuperuser`,
then go to `/admin/` -> Users -> open that user -> set
**Role = Super Admin**.

This is enforced both in the UI (buttons are hidden) and in the
server-side views themselves (`accounts/permissions.py`) -- so it's
not just a cosmetic restriction, it blocks the underlying action too.

**Important — one-time migration step:** this update added a new
`staff` field to the Company model, a uniqueness constraint on Fixed
Assets, and made **email unique** on the User model (needed for
email-based login). If you already ran `migrate` before, run this
once more after updating your files:
```bash
python manage.py makemigrations
python manage.py migrate
```
(The `setup.sh` / `setup.bat` scripts already do this automatically
for a fresh install.) If migration fails because two existing accounts
share the same email, fix that in `/admin/` first (give each user a
distinct email), then re-run the migration.

## ✅ Duplicate-entry validation (fixed)

Previously, entering a **duplicate Account Code**, **duplicate
Inventory SKU**, or **duplicate Fixed Asset name** within the same
company would either crash with a raw database error or (for Fixed
Assets) silently create a confusing duplicate. Now all three show a
clear, friendly message right on the form, e.g.:

> Account code "1000" is already registered for this company. Please use a different code.

This is enforced at both the form level (immediate, friendly feedback)
and the database level (a real safety net, so it can't be bypassed).
Two form templates (`inventory/item_form.html` and
`assets/asset_form.html`) were also missing their error-display block
entirely — fixed as part of this update so validation messages
actually reach the screen instead of failing silently.

---

## What's built so far (Phase 1 + 2 — fully working)

- **Accounts app**: custom user model with roles (Super Admin, Company
  Owner, Accountant, Employee), register, login, logout, change
  password, full forgot-password email flow, edit profile.
- **Companies app**: full CRUD, search, multi-company support with a
  company switcher in the dashboard. Each company stores its own
  **IFRS / GAAP / Other** accounting standard.
- **Accounting app**: Chart of Accounts (CRUD, search, filter by
  type), Journal Entries (debit = credit by design), auto-generated
  General Ledger with running balance, auto-calculated Trial Balance,
  **Profit & Loss Statement**, and **Balance Sheet** (with an
  assets = liabilities + equity balance check).
- **Inventory app**: items with SKU, quantity, cost/selling price,
  low-stock alert.
- **Fixed Assets app**: full CRUD with automatic **straight-line** and
  **declining-balance depreciation** calculated live.
- **Transactions app**: full CRUD for **Customers** and **Suppliers**,
  **Sales Invoices** and **Purchase Bills** with multi-line item
  formsets, **Payments** (with partial-payment tracking), and
  **Budget** (budget vs actual with variance).
- **Dashboard**: cards (companies, revenue, expenses, profit) +
  Chart.js revenue-vs-expenses chart + recent activity feed.
- **Reports app**: Trial Balance export to PDF (ReportLab) and Excel
  (OpenPyXL).
- **API app**: Django REST Framework endpoints for companies,
  accounts, journal entries, inventory, customers, suppliers, plus
  token-based register/login.
- **AI**: a starter fraud-detection model (scikit-learn IsolationForest)
  with a training script and a `score_journal_entry()` helper ready to
  wire into a view.
- **Admin panel**: every model above is registered in Django Admin.
- **Database**: SQLite3 only (Django's default), via `db.sqlite3` —
  no MySQL/SQL Server anywhere, exactly as required.

## What's next (not yet built)

- DataTables sorting/search is wired in globally (see `data-datatable`
  attribute on tables) — pagination length, column-specific search,
  and export buttons could be extended further per table if desired.
- Real bankruptcy training data: `train_bankruptcy_model.py` currently
  uses synthetic data; swap in a labeled dataset (e.g. the public
  Taiwan Economic Journal bankruptcy dataset) once you want a
  production-grade model.
- Revenue-growth scoring in the Business Stability Index is currently
  a neutral placeholder (50) since it needs period-over-period
  history tracking — extend `ai_models/business_stability.py` to
  compare this month/quarter vs. the last once you have that data.

## AI Modules — all four are now wired in

1. **Fraud Detection** (`ai_models/train_fraud_model.py` +
   `ai_models/predict.py`) — scores every new Journal Entry
   automatically (see `accounting/views.py: journal_create`) and shows
   a risk score in a flash message. Also scans your last 15 entries on
   the **AI Reports** page.
2. **Business Stability Index** (`ai_models/business_stability.py`) —
   a rule-based scoring engine (not ML) that combines liquidity,
   profitability, cash flow, revenue growth, expense control, and debt
   ratio into one 0-100 score with a status label, computed live from
   your Chart of Accounts balances.
3. **Bankruptcy Prediction** (`ai_models/train_bankruptcy_model.py` +
   `ai_models/predict_bankruptcy.py`) — a logistic regression trained
   on the same six ratios, outputting a probability and risk level.
4. **Cash Flow Prediction** (`ai_models/cash_flow_prediction.py`) —
   aggregates your real Journal Entries into monthly income/expense
   totals and fits a linear regression to project next month; falls
   back to an average-based estimate if you have less than 3 months
   of data.

All four show up together on the **AI Reports** page
(`/reports/ai/`), including a Chart.js cash-flow forecast chart.

### To enable AI scoring, train the two ML models once:
```bash
python ai_models/train_fraud_model.py
python ai_models/train_bankruptcy_model.py
```
The Business Stability Index and Cash Flow Prediction work immediately
with no training step, since they're calculated directly from your
live accounting data.

---

## Step-by-Step Setup (Beginner Friendly)

### 1. Install Python
Make sure you have **Python 3.10+** installed. Check with:
```bash
python3 --version
```
If not installed, download from https://www.python.org/downloads/

### 2. Open the project folder
Unzip the file you downloaded, then open a terminal inside
`AI_Finance_Manager/`.

### 3. Create a virtual environment (keeps this project's packages separate)
```bash
python3 -m venv venv
```
Activate it:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

You'll know it worked because your terminal prompt will show `(venv)`.

### 4. Install the required packages
```bash
pip install -r requirements.txt
```

### 5. Create the SQLite database
Django will read your models and build the database tables:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create an admin (superuser) account
```bash
python manage.py createsuperuser
```
Follow the prompts (username, email, password).

### 7. (Optional but recommended) Load demo data
This creates a demo Company Owner, a demo company, a chart of
accounts, 4 months of journal entries, a customer, a supplier, an
inventory item, a fixed asset, a budget line, and a demo Employee
account already granted access to that company — so every module
(including AI Reports, Cash Flow Prediction, and the new staff-access
flow) has something to show immediately:
```bash
python manage.py seed_demo_data
```
This creates two logins:
- **Company Owner:** username `demo` / password `demo12345`
- **Employee:** email `employee@example.com` / password `employee12345`
  (log in with the email in the "Email or Username" field)

### 8. Train the AI models (one-time step)
```bash
python ai_models/train_fraud_model.py
python ai_models/train_bankruptcy_model.py
```
This saves `fraud_model.joblib` and `bankruptcy_model.joblib` inside
`ai_models/`. The Business Stability Index and Cash Flow Prediction
don't need training — they compute live from your accounting data.

### 9. Run the development server
```bash
python manage.py runserver
```
Open your browser at **http://127.0.0.1:8000/**

- Log in with `demo` / `demo12345` (or register a new account at
  `/accounts/register/`)
- Visit `/admin/` and log in with the superuser you created in Step 6
  to manage every module directly.
- Visit **AI Reports** in the sidebar to see all four AI modules
  together: fraud scan, stability index, bankruptcy probability, and
  the cash-flow forecast chart.

---

## How the project is organized (so you can keep building)

```
AI_Finance_Manager/
├── manage.py
├── requirements.txt
├── financeproject/      <- settings.py, urls.py (the project "hub")
├── accounts/             <- users, roles, login/register/profile
├── companies/             <- multi-company CRUD
├── accounting/             <- chart of accounts, journal, ledger, trial balance
├── inventory/               <- stock items + low stock alerts
├── assets/                   <- fixed assets + depreciation (models only)
├── transactions/               <- customers/suppliers/sales/purchase/payments/budget (models only)
├── reports/                     <- PDF/Excel export views
├── dashboard/                    <- home page with cards + charts
├── api/                            <- Django REST Framework endpoints
├── ai_models/                       <- fraud detection training + prediction
├── templates/                        <- shared base.html (sidebar/navbar/footer)
└── static/                            <- css/js
```

### The pattern every module follows
Each Django app has the same five files — once you understand one
app, you understand them all:
1. `models.py` — defines the database table(s)
2. `forms.py` — defines the HTML form for creating/editing
3. `views.py` — the logic (list, create, update, delete)
4. `urls.py` — maps a URL like `/inventory/add/` to a view
5. `templates/<app>/*.html` — the actual pages, extending `base.html`

To finish the **transactions** module (customers, sales invoices,
etc.), copy the `inventory` app's `views.py`/`urls.py`/templates as a
template and repeat for each model in `transactions/models.py`.

---

## Remaining polish ideas (optional)
1. Add a proper Cash Flow *Statement* (Operating/Investing/Financing
   breakdown) — currently the Cash Flow *Prediction* AI module covers
   forecasting, but a formal 3-section statement report isn't built
   yet. Follow the same pattern as `profit_and_loss` / `balance_sheet`
   in `accounting/views.py`.
2. Add Customer/Supplier statements (list of invoices/bills per
   customer or supplier) for a fuller CRM-style view.
3. Swap the bankruptcy model's synthetic training data for a real
   labeled dataset once available (see AI Modules section above).
4. Add row-level actions (mark invoice as paid, auto-create a Payment)
   linking the Sales Invoice and Payment modules together.

Everything else from the original spec — auth & roles, multi-company,
full double-entry accounting (COA, journal, ledger, trial balance,
P&L, balance sheet), inventory, fixed assets with depreciation, sales/
purchase/payments/budget, dashboard, PDF/Excel export, REST API, all
4 AI modules, and the admin panel — is built and working end-to-end.

If you'd like, tell me which of the polish items to tackle next and
I'll continue in the same style.
