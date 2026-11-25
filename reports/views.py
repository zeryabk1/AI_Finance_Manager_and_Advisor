from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from accounting.views import get_active_company
from accounting.models import Account, JournalEntry
from django.db.models import Sum


def _pdf_canvas(response, title, company):
    """Start a new ReportLab PDF page with a standard header. Returns (canvas, width, height, y)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas

    p = pdf_canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, f"{title} - {company.name if company else ''}")
    y -= 30
    return p, width, height, y


def _pdf_table_header(p, y, columns):
    """columns: list of (label, x_position)"""
    p.setFont('Helvetica-Bold', 10)
    for label, x in columns:
        p.drawString(x, y, label)
    return y - 15


def _pdf_new_page_if_needed(p, y, width, height):
    if y < 60:
        p.showPage()
        return height - 50
    return y


def _excel_workbook(sheet_title, header_row):
    import openpyxl
    from openpyxl.styles import Font

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(header_row)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    return wb, ws


def _excel_response(wb, filename):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
def trial_balance_pdf(request):
    """Export Trial Balance as PDF using ReportLab."""
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="trial_balance.pdf"'

    p, width, height, y = _pdf_canvas(response, 'Trial Balance', company)
    y = _pdf_table_header(p, y, [('Code', 50), ('Account', 120), ('Debit', 350), ('Credit', 450)])
    p.setFont('Helvetica', 10)

    total_debit = total_credit = 0
    for account in accounts:
        debit_total = account.debit_entries.aggregate(total=Sum('amount'))['total'] or 0
        credit_total = account.credit_entries.aggregate(total=Sum('amount'))['total'] or 0
        net = debit_total - credit_total
        debit_col = net if net > 0 else 0
        credit_col = -net if net < 0 else 0
        total_debit += debit_col
        total_credit += credit_col

        p.drawString(50, y, account.code)
        p.drawString(120, y, account.name[:35])
        p.drawString(350, y, f"{debit_col:.2f}")
        p.drawString(450, y, f"{credit_col:.2f}")
        y -= 15
        y = _pdf_new_page_if_needed(p, y, width, height)

    y -= 10
    p.setFont('Helvetica-Bold', 10)
    p.drawString(350, y, f"{total_debit:.2f}")
    p.drawString(450, y, f"{total_credit:.2f}")

    p.showPage()
    p.save()
    return response


@login_required
def trial_balance_excel(request):
    """Export Trial Balance as Excel using OpenPyXL."""
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()

    wb, ws = _excel_workbook('Trial Balance', ["Code", "Account", "Debit", "Credit"])

    total_debit = total_credit = 0
    for account in accounts:
        debit_total = account.debit_entries.aggregate(total=Sum('amount'))['total'] or 0
        credit_total = account.credit_entries.aggregate(total=Sum('amount'))['total'] or 0
        net = debit_total - credit_total
        debit_col = float(net) if net > 0 else 0
        credit_col = float(-net) if net < 0 else 0
        total_debit += debit_col
        total_credit += credit_col
        ws.append([account.code, account.name, debit_col, credit_col])

    ws.append(["", "TOTAL", total_debit, total_credit])
    return _excel_response(wb, 'trial_balance.xlsx')


@login_required
def general_ledger_pdf(request):
    """Export General Ledger as PDF - one section per account."""
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="general_ledger.pdf"'
    p, width, height, y = _pdf_canvas(response, 'General Ledger', company)

    for account in accounts:
        if y < 120:
            p.showPage()
            y = height - 50
        p.setFont('Helvetica-Bold', 11)
        p.drawString(50, y, f"{account.code} - {account.name}")
        y -= 18
        y = _pdf_table_header(p, y, [('Date', 50), ('Description', 130), ('Debit', 350), ('Credit', 420), ('Balance', 490)])
        p.setFont('Helvetica', 9)

        from accounting.ledger import build_ledger
        data = build_ledger(account)
        for row in data['entries']:
            p.drawString(50, y, str(row['date']))
            p.drawString(130, y, row['description'][:35])
            p.drawString(350, y, f"{row['debit']:.2f}" if row['debit'] is not None else '')
            p.drawString(420, y, f"{row['credit']:.2f}" if row['credit'] is not None else '')
            p.drawString(490, y, f"{row['balance']:.2f} {row['side']}")
            y -= 14
            y = _pdf_new_page_if_needed(p, y, width, height)
        if not data['entries']:
            p.drawString(50, y, "No transactions.")
            y -= 14
        closing = data['closing']
        p.setFont('Helvetica-Bold', 9)
        p.drawString(420, y, "Closing:")
        p.drawString(490, y, f"{closing['balance']:.2f} {closing['side']}" + ("  (unusual)" if closing['unusual'] else ""))
        y -= 24

    p.showPage()
    p.save()
    return response


@login_required
def general_ledger_excel(request):
    """Export General Ledger as Excel - one sheet per account."""
    import openpyxl
    from openpyxl.styles import Font

    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    for account in accounts:
        # Excel sheet names max 31 chars, no special characters
        safe_title = f"{account.code} {account.name}"[:31]
        ws = wb.create_sheet(title=safe_title or account.code)
        ws.append(["Date", "Description", "Debit", "Credit", "Balance"])
        for cell in ws[1]:
            cell.font = Font(bold=True)

        from accounting.ledger import build_ledger
        data = build_ledger(account)
        for row in data['entries']:
            ws.append([
                str(row['date']), row['description'],
                float(row['debit']) if row['debit'] is not None else None,
                float(row['credit']) if row['credit'] is not None else None,
                f"{row['balance']:.2f} {row['side']}",
            ])
        closing = data['closing']
        ws.append(["", "Closing Balance", "", "",
                   f"{closing['balance']:.2f} {closing['side']}" + (" (unusual)" if closing['unusual'] else "")])

    if not wb.sheetnames:
        wb.create_sheet(title="General Ledger")

    return _excel_response(wb, 'general_ledger.xlsx')


@login_required
def profit_loss_pdf(request):
    """Export the Income Statement (IFRS or US GAAP layout, per company setting) as PDF."""
    from accounting.standards import build_income_statement
    company = get_active_company(request)
    inc = build_income_statement(company)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="income_statement.pdf"'
    p, width, height, y = _pdf_canvas(response, inc['title'], company)
    p.setFont('Helvetica-Oblique', 8)
    p.drawString(50, y + 8, f"{company.standard_label if company else ''} presentation")
    y -= 6
    for l in inc['lines']:
        kind, amt = l['kind'], l['amount']
        if kind == 'heading':
            y -= 4
            p.setFont('Helvetica-Bold', 10)
            p.drawString(50, y, l['label'])
        elif kind == 'item':
            p.setFont('Helvetica', 10)
            p.drawString(70, y, l['label'][:50])
            p.drawRightString(520, y, f"{amt:,.2f}")
        else:
            p.setFont('Helvetica-Bold', 11 if kind == 'total' else 10)
            p.drawString(55, y, l['label'][:55])
            p.drawRightString(520, y, f"{amt:,.2f}")
        y -= 15
        y = _pdf_new_page_if_needed(p, y, width, height)
    p.showPage()
    p.save()
    return response


@login_required
def profit_loss_excel(request):
    """Export the Income Statement (IFRS or US GAAP layout) as Excel."""
    from openpyxl.styles import Font
    from accounting.standards import build_income_statement
    company = get_active_company(request)
    inc = build_income_statement(company)

    wb, ws = _excel_workbook(inc['title'][:31], ["Line", "Amount"])
    ws.append([f"{company.standard_label if company else ''} presentation", ""])
    for l in inc['lines']:
        label = ("    " + l['label']) if l['kind'] == 'item' else l['label']
        ws.append([label, float(l['amount']) if l['amount'] is not None else None])
        if l['kind'] in ('heading', 'subtotal', 'total'):
            for c in ws[ws.max_row]:
                c.font = Font(bold=True)
    ws.column_dimensions['A'].width = 55
    ws.column_dimensions['B'].width = 18
    return _excel_response(wb, 'income_statement.xlsx')


@login_required
def balance_sheet_pdf(request):
    """Export the Balance Sheet / Statement of Financial Position (per company standard) as PDF."""
    from accounting.standards import build_balance_sheet
    company = get_active_company(request)
    bs = build_balance_sheet(company)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="balance_sheet.pdf"'
    p, width, height, y = _pdf_canvas(response, bs['title'], company)
    p.setFont('Helvetica-Oblique', 8)
    p.drawString(50, y + 8, f"{company.standard_label if company else ''} presentation")
    y -= 6

    def line(label, amount, x, font='Helvetica', size=10):
        nonlocal y
        p.setFont(font, size)
        p.drawString(x, y, label[:55])
        p.drawRightString(520, y, f"{amount:,.2f}")
        y -= 14
        y = _pdf_new_page_if_needed(p, y, width, height)

    for g in bs['groups']:
        p.setFont('Helvetica-Bold', 11)
        p.drawString(50, y, g['heading'])
        y -= 17
        for sec in g['sections']:
            p.setFont('Helvetica-Bold', 10)
            p.drawString(60, y, sec['title'])
            y -= 14
            for r in sec['rows']:
                line(r['name'], r['amount'], 80)
            line(f"Total {sec['title'].lower()}", sec['total'], 60, 'Helvetica-Bold')
            y -= 4
        line(g['total_label'], g['total'], 50, 'Helvetica-Bold', 11)
        y -= 10

    line('Total assets', bs['total_assets'], 50, 'Helvetica-Bold', 11)
    line(bs['grand_total_label'], bs['total_equity_liabilities'], 50, 'Helvetica-Bold', 11)
    p.setFont('Helvetica', 10)
    p.drawString(50, y - 6, "Balanced" if bs['balanced'] else "NOT balanced - review entries")
    p.showPage()
    p.save()
    return response


@login_required
def balance_sheet_excel(request):
    """Export the Balance Sheet / Statement of Financial Position (per company standard) as Excel."""
    from openpyxl.styles import Font
    from accounting.standards import build_balance_sheet
    company = get_active_company(request)
    bs = build_balance_sheet(company)

    wb, ws = _excel_workbook(bs['title'][:31], ["Line", "Amount"])
    ws.append([f"{company.standard_label if company else ''} presentation", ""])
    bold = lambda: [setattr(c, 'font', Font(bold=True)) for c in ws[ws.max_row]]
    for g in bs['groups']:
        ws.append([g['heading'], None]); bold()
        for sec in g['sections']:
            ws.append(["  " + sec['title'], None]); bold()
            for r in sec['rows']:
                ws.append(["      " + r['name'], float(r['amount'])])
            ws.append([f"  Total {sec['title'].lower()}", float(sec['total'])]); bold()
        ws.append([g['total_label'], float(g['total'])]); bold()
        ws.append([])
    ws.append(["Total assets", float(bs['total_assets'])]); bold()
    ws.append([bs['grand_total_label'], float(bs['total_equity_liabilities'])]); bold()
    ws.column_dimensions['A'].width = 55
    ws.column_dimensions['B'].width = 18
    return _excel_response(wb, 'balance_sheet.xlsx')


@login_required
def fixed_assets_pdf(request):
    """Export Fixed Assets register as PDF."""
    company = get_active_company(request)
    assets = company.fixed_assets.all() if company else []

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fixed_assets.pdf"'
    p, width, height, y = _pdf_canvas(response, 'Fixed Assets', company)
    y = _pdf_table_header(p, y, [
        ('Asset', 50), ('Purchase Date', 170), ('Cost', 270),
        ('Method', 340), ('Annual Depr.', 430), ('Book Value', 510),
    ])
    p.setFont('Helvetica', 9)

    total_book_value = 0
    for a in assets:
        total_book_value += a.current_book_value
        p.drawString(50, y, a.asset_name[:25])
        p.drawString(170, y, str(a.purchase_date))
        p.drawString(270, y, f"{a.purchase_price:.2f}")
        p.drawString(340, y, a.get_depreciation_method_display())
        p.drawString(430, y, f"{a.annual_depreciation:.2f}")
        p.drawString(510, y, f"{a.current_book_value:.2f}")
        y -= 15
        y = _pdf_new_page_if_needed(p, y, width, height)

    y -= 10
    p.setFont('Helvetica-Bold', 10)
    p.drawString(50, y, "Total Book Value")
    p.drawString(510, y, f"{total_book_value:.2f}")

    p.showPage()
    p.save()
    return response


@login_required
def fixed_assets_excel(request):
    """Export Fixed Assets register as Excel."""
    company = get_active_company(request)
    assets = company.fixed_assets.all() if company else []

    wb, ws = _excel_workbook('Fixed Assets', [
        "Asset", "Purchase Date", "Cost", "Method",
        "Annual Depreciation", "Accumulated Depreciation", "Book Value",
    ])

    total_book_value = 0
    for a in assets:
        total_book_value += float(a.current_book_value)
        ws.append([
            a.asset_name, str(a.purchase_date), float(a.purchase_price),
            a.get_depreciation_method_display(), float(a.annual_depreciation),
            float(a.accumulated_depreciation), float(a.current_book_value),
        ])
    ws.append(["", "", "", "", "", "Total Book Value", total_book_value])

    return _excel_response(wb, 'fixed_assets.xlsx')


@login_required
def ai_dashboard(request):
    """
    AI Reports page: Business Stability Index, Bankruptcy Prediction,
    Cash Flow Prediction, and a recent Fraud Detection scan.
    """
    company = get_active_company(request)
    context = {'company': company}

    if not company:
        return render(request, 'reports/ai_dashboard.html', context)

    # --- Business Stability Index (rule-based, always available) ---
    from ai_models.business_stability import calculate_stability_index
    stability = calculate_stability_index(company)
    context['stability'] = stability

    # --- Bankruptcy Prediction (auto-trains on first use) ---
    from ai_models.predict_bankruptcy import predict_bankruptcy
    context['bankruptcy'] = predict_bankruptcy(stability)

    # --- Cash Flow Prediction ---
    from ai_models.cash_flow_prediction import predict_next_month_cash_flow
    context['cash_flow'] = predict_next_month_cash_flow(company)

    # --- Fraud Detection scan of recent journal entries (auto-trains on first use) ---
    from ai_models.predict import score_journal_entry
    recent_entries = JournalEntry.objects.filter(company=company).order_by('-date', '-created_at')[:15]
    fraud_rows = []
    for entry in recent_entries:
        frequency = JournalEntry.objects.filter(
            company=company, debit_account=entry.debit_account, credit_account=entry.credit_account
        ).count()
        result = score_journal_entry(float(entry.amount), frequency)
        fraud_rows.append({'entry': entry, **result})
    context['fraud_rows'] = fraud_rows

    return render(request, 'reports/ai_dashboard.html', context)
