import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from app.services.rules        import get_monthly_summary, get_savings_forecast
from app.services.health_score import compute_health_score


# ── Colour palette ────────────────────────────────────────
TEAL       = colors.HexColor('#63D9B4')
DARK_BG    = colors.HexColor('#0F1923')
CARD_BG    = colors.HexColor('#141F2B')
MUTED      = colors.HexColor('#8FA3B0')
WHITE      = colors.white
RED        = colors.HexColor('#FCA5A5')
YELLOW     = colors.HexColor('#FCD34D')


def build_styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        'WW_Title',
        parent=base['Title'],
        fontSize=24,
        textColor=WHITE,
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        'WW_Sub',
        parent=base['Normal'],
        fontSize=11,
        textColor=TEAL,
        fontName='Helvetica',
        spaceAfter=16,
    )
    section = ParagraphStyle(
        'WW_Section',
        parent=base['Normal'],
        fontSize=13,
        textColor=TEAL,
        fontName='Helvetica-Bold',
        spaceBefore=16,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        'WW_Body',
        parent=base['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#C5D3DB'),
        fontName='Helvetica',
        spaceAfter=4,
        leading=15,
    )
    small = ParagraphStyle(
        'WW_Small',
        parent=base['Normal'],
        fontSize=9,
        textColor=MUTED,
        fontName='Helvetica',
        spaceAfter=2,
    )
    bold_body = ParagraphStyle(
        'WW_Bold',
        parent=base['Normal'],
        fontSize=10,
        textColor=WHITE,
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    score_big = ParagraphStyle(
        'WW_Score',
        parent=base['Normal'],
        fontSize=36,
        textColor=TEAL,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    centered = ParagraphStyle(
        'WW_Centered',
        parent=base['Normal'],
        fontSize=10,
        textColor=MUTED,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    return {
        'title':     title,
        'subtitle':  subtitle,
        'section':   section,
        'body':      body,
        'small':     small,
        'bold_body': bold_body,
        'score_big': score_big,
        'centered':  centered,
    }


def _table_style(header_bg=None):
    if header_bg is None:
        header_bg = TEAL
    return TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0),  header_bg),
        ('TEXTCOLOR',   (0, 0), (-1, 0),  DARK_BG),
        ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, 0),  9),
        ('ALIGN',       (0, 0), (-1, 0),  'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.HexColor('#1A2A38')]),
        ('TEXTCOLOR',   (0, 1), (-1, -1), colors.HexColor('#C5D3DB')),
        ('FONTNAME',    (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',    (0, 1), (-1, -1), 9),
        ('ALIGN',       (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWPADDING',  (0, 0), (-1, -1), 6),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.HexColor('#1E3A4A')),
        ('ROUNDEDCORNERS', [4]),
    ])


def generate_pdf(user, ai_summary=None):
    """
    Generates a full monthly PDF report for the user.
    Returns a BytesIO buffer ready to be sent as a file download.
    """
    buffer  = io.BytesIO()
    doc     = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f'WalletWizzard Report — {datetime.now().strftime("%B %Y")}',
    )

    summary  = get_monthly_summary(user.id)
    health   = compute_health_score(user.id)
    forecast = get_savings_forecast(user.id, months=12)
    styles   = build_styles()
    now      = datetime.now()
    story    = []

    # ── Cover ─────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('WalletWizzard', styles['title']))
    story.append(Paragraph(
        f'Monthly Financial Report — {now.strftime("%B %Y")}',
        styles['subtitle']
    ))
    story.append(Paragraph(
        f'Prepared for: {user.username}  |  Generated: {now.strftime("%d %b %Y %H:%M")}',
        styles['small']
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=TEAL, spaceAfter=16))

    # ── 1. Summary metrics ────────────────────────────────
    story.append(Paragraph('1. Monthly Overview', styles['section']))

    metrics_data = [
        ['Metric', 'Amount'],
        ['Monthly Income',    f"${summary['total_income']:.2f}"],
        ['Total Expenses',    f"${summary['total_expense']:.2f}"],
        ['Total Budgeted',    f"${summary['total_planned']:.2f}"],
        ['Net Savings',       f"${summary['savings']:.2f}"],
        ['Savings Rate',      f"{summary['savings_rate']}%"],
        ['Subscription Cost', f"${summary['sub_cost']:.2f}/mo ({summary['sub_count']} active)"],
    ]

    metrics_table = Table(metrics_data, colWidths=[9*cm, 7*cm])
    metrics_table.setStyle(_table_style())
    story.append(metrics_table)

    # ── 2. Health score ───────────────────────────────────
    story.append(Paragraph('2. Financial Health Score', styles['section']))
    story.append(Paragraph(str(health['score']), styles['score_big']))
    story.append(Paragraph(
        f"out of 100 — {health['label']}",
        styles['centered']
    ))
    story.append(Spacer(1, 0.3*cm))

    factor_data = [['Factor', 'Score', 'Detail']]
    for f in health['factors']:
        color_tag = '✓' if f['score'] >= 70 else ('~' if f['score'] >= 40 else '✗')
        factor_data.append([
            f['name'],
            f"{color_tag} {f['score']}/100",
            f['note']
        ])

    factor_table = Table(factor_data, colWidths=[4.5*cm, 2.5*cm, 9*cm])
    factor_table.setStyle(_table_style())
    story.append(factor_table)

    # ── 3. Budget vs actual ───────────────────────────────
    story.append(Paragraph('3. Budget vs Actual Spending', styles['section']))

    if summary['budget_by_category']:
        budget_data = [['Category', 'Planned', 'Actual', 'Status']]
        for cat, planned in summary['budget_by_category'].items():
            actual = summary['by_category'].get(cat, 0)
            over   = actual - planned
            status = f'+${over:.2f} OVER' if over > 0 else f'${abs(over):.2f} left'
            budget_data.append([
                cat,
                f'${planned:.2f}',
                f'${actual:.2f}',
                status
            ])
        budget_table = Table(budget_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 5*cm])
        budget_table.setStyle(_table_style())
        story.append(budget_table)
    else:
        story.append(Paragraph('No budgets set for this month.', styles['body']))

    # ── 4. Savings goals ──────────────────────────────────
    story.append(Paragraph('4. Savings Goals', styles['section']))

    if summary['goals']:
        goals_data = [['Goal', 'Target', 'Saved', 'Progress', 'ETA']]
        for g in summary['goals']:
            goals_data.append([
                g.name,
                f'${g.target_amount:.2f}',
                f'${g.saved_amount:.2f}',
                f'{g.progress_pct}%',
                f'{g.estimated_months} mo' if g.estimated_months else '—'
            ])
        goals_table = Table(goals_data, colWidths=[4*cm, 3*cm, 3*cm, 2.5*cm, 3.5*cm])
        goals_table.setStyle(_table_style())
        story.append(goals_table)
    else:
        story.append(Paragraph('No active savings goals.', styles['body']))

    # ── 5. 12-month forecast ──────────────────────────────
    story.append(Paragraph('5. 12-Month Savings Forecast', styles['section']))
    story.append(Paragraph(
        f"Monthly savings: ${forecast[0]['monthly']:.2f}/mo — "
        f"Projected total in 12 months: ${forecast[-1]['cumulative']:.2f}",
        styles['body']
    ))
    story.append(Spacer(1, 0.3*cm))

    forecast_data = [['Month', 'Monthly Savings', 'Cumulative Total']]
    for f in forecast:
        forecast_data.append([
            f['month'],
            f"${f['monthly']:.2f}",
            f"${f['cumulative']:.2f}"
        ])
    forecast_table = Table(forecast_data, colWidths=[5*cm, 5*cm, 6*cm])
    forecast_table.setStyle(_table_style())
    story.append(forecast_table)

    # ── 6. AI summary (optional) ──────────────────────────
    if ai_summary:
        story.append(Paragraph('6. Wizzard AI Insights', styles['section']))
        story.append(HRFlowable(width='100%', thickness=0.3, color=TEAL, spaceAfter=8))
        # Clean up markdown-style formatting
        clean = ai_summary.replace('**', '').replace('*', '').replace('#', '')
        for line in clean.split('\n'):
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles['body']))
                story.append(Spacer(1, 0.1*cm))

    # ── Footer ────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=0.3, color=MUTED, spaceAfter=6))
    story.append(Paragraph(
        f'WalletWizzard — AI-Powered Financial Intelligence  |  '
        f'Report generated {now.strftime("%d %b %Y")}  |  '
        f'Data is for informational purposes only.',
        styles['small']
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer