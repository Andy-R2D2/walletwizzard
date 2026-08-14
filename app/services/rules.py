import math
from app.models.expense import Expense
from app.models.income import Income
from app.models.subscription import Subscription
from app.models.goal import Goal
from sqlalchemy import extract
from datetime import datetime


def get_current_month_data(user_id):
    """Get all expenses and income for the current month."""
    now = datetime.now()
    month, year = now.month, now.year

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == month,
        extract('year',  Expense.date) == year
    ).all()

    incomes = Income.query.filter(
        Income.user_id == user_id,
        extract('month', Income.date) == month,
        extract('year',  Income.date) == year
    ).all()

    return expenses, incomes


def check_overspending(user_id):
    """
    Rule: compare Budget.planned vs sum of Expense.amount_actual
    per category for the current month.
    """
    from app.models.budget import Budget
    now = datetime.now()

    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=now.month,
        year=now.year
    ).all()

    if not budgets:
        return []

    expenses, _ = get_current_month_data(user_id)

    # Sum actuals by category
    actual_by_cat = {}
    for e in expenses:
        actual_by_cat[e.category] = round(
            actual_by_cat.get(e.category, 0) + e.amount_actual, 2
        )

    alerts = []
    for b in budgets:
        actual = actual_by_cat.get(b.category, 0)
        if actual > b.planned:
            overspend = round(actual - b.planned, 2)
            pct       = round((overspend / b.planned) * 100, 1)
            alerts.append({
                'type':      'overspend',
                'category':  b.category,
                'actual':    actual,
                'planned':   b.planned,
                'overspend': overspend,
                'pct':       pct,
                'message':   f'Your {b.category} spending is ${overspend} over budget this month (+{pct}%).'
            })

    return alerts

def check_subscription_load(user_id):
    """
    Rule: if user has 5+ active subscriptions AND monthly income
    is less than 3x the subscription total → alert.
    """
    alerts = []
    subs = Subscription.query.filter_by(user_id=user_id, active=True).all()
    count = len(subs)

    if count == 0:
        return alerts

    monthly_sub_cost = sum(
        s.amount if s.billing == 'monthly' else s.amount / 12
        for s in subs
    )

    _, incomes = get_current_month_data(user_id)
    monthly_income = sum(i.amount for i in incomes)

    if count >= 5:
        alerts.append({
            'type':    'subscription_count',
            'count':   count,
            'cost':    round(monthly_sub_cost, 2),
            'message': f'You have {count} active subscriptions costing ${monthly_sub_cost:.2f}/month. Consider reviewing them.'
        })

    if monthly_income > 0 and monthly_sub_cost > (monthly_income * 0.2):
        pct = round((monthly_sub_cost / monthly_income) * 100, 1)
        alerts.append({
            'type':    'subscription_ratio',
            'cost':    round(monthly_sub_cost, 2),
            'income':  round(monthly_income, 2),
            'pct':     pct,
            'message': f'Subscriptions eat {pct}% of your monthly income (${monthly_sub_cost:.2f} / ${monthly_income:.2f}).'
        })

    return alerts


def check_savings_rate(user_id):
    """
    Rule: savings rate = (income - expenses) / income.
    Alert if below 10%.
    """
    alerts = []
    expenses, incomes = get_current_month_data(user_id)

    total_income  = sum(i.amount for i in incomes)
    total_expense = sum(e.amount_actual for e in expenses)

    if total_income == 0:
        return alerts

    savings      = total_income - total_expense
    savings_rate = round((savings / total_income) * 100, 1)

    if savings_rate < 10:
        alerts.append({
            'type':         'low_savings',
            'savings_rate': savings_rate,
            'savings':      round(savings, 2),
            'income':       round(total_income, 2),
            'message':      f'Your savings rate is {savings_rate}% this month. Try to reach at least 10%.'
        })

    return alerts


def check_anomalies(user_id):
    """
    Rule: detect if any single expense category this month
    is more than 240% of the same category last month.
    """
    from sqlalchemy import extract as ex
    alerts = []
    now   = datetime.now()
    month = now.month
    year  = now.year

    last_month = month - 1 if month > 1 else 12
    last_year  = year if month > 1 else year - 1

    current = Expense.query.filter(
        Expense.user_id == user_id,
        ex('month', Expense.date) == month,
        ex('year',  Expense.date) == year
    ).all()

    last = Expense.query.filter(
        Expense.user_id == user_id,
        ex('month', Expense.date) == last_month,
        ex('year',  Expense.date) == last_year
    ).all()

    # Sum by category
    def sum_by_cat(rows):
        d = {}
        for e in rows:
            d[e.category] = d.get(e.category, 0) + e.amount_actual
        return d

    current_by_cat = sum_by_cat(current)
    last_by_cat    = sum_by_cat(last)

    for cat, amount in current_by_cat.items():
        prev = last_by_cat.get(cat, 0)
        if prev > 0:
            change_pct = round(((amount - prev) / prev) * 100, 1)
            if change_pct >= 240:
                alerts.append({
                    'type':       'anomaly',
                    'category':   cat,
                    'current':    round(amount, 2),
                    'previous':   round(prev, 2),
                    'change_pct': change_pct,
                    'message':    f'Unusually high {cat} spending this month (+{change_pct}% vs last month).'
                })

    return alerts


def run_all_rules(user_id):
    """
    Run every rule and return a combined list of alerts.
    Each alert has at minimum: type, message.
    """
    alerts = []
    alerts += check_overspending(user_id)
    alerts += check_subscription_load(user_id)
    alerts += check_savings_rate(user_id)
    alerts += check_anomalies(user_id)
    return alerts


def run_all_insights(user_id):
    """
    Runs rules + anomaly detection + goal recalculation.
    Returns alerts and goal_insights separately.
    """
    alerts        = run_all_rules(user_id)
    alerts       += detect_anomalies(user_id)
    goal_insights = recalculate_all_goals(user_id)
    return alerts, goal_insights


def get_monthly_summary(user_id):
    """
    Returns a clean summary dict used by the dashboard and AI engine.
    """
    from app.models.budget import Budget

    expenses, incomes = get_current_month_data(user_id)
    now = datetime.now()

    total_income  = round(sum(i.amount for i in incomes), 2)
    total_expense = round(sum(e.amount_actual for e in expenses), 2)
    savings       = round(total_income - total_expense, 2)
    savings_rate  = round((savings / total_income * 100), 1) if total_income > 0 else 0.0

    subs = Subscription.query.filter_by(user_id=user_id, active=True).all()
    sub_cost = round(sum(
        s.amount if s.billing == 'monthly' else s.amount / 12
        for s in subs
    ), 2)

    goals = Goal.query.filter_by(user_id=user_id, achieved=False).all()

    # Spending by category
    by_category = {}
    for e in expenses:
        by_category[e.category] = round(
            by_category.get(e.category, 0) + e.amount_actual, 2
        )

    # Budget by category
    budgets = Budget.query.filter_by(
        user_id=user_id,
        month=now.month,
        year=now.year
    ).all()
    budget_by_category = {b.category: b.planned for b in budgets}
    total_planned = round(sum(budget_by_category.values()), 2)

    return {
        'total_income':        total_income,
        'total_expense':       total_expense,
        'total_planned':       total_planned,
        'savings':             savings,
        'savings_rate':        savings_rate,
        'sub_cost':            sub_cost,
        'sub_count':           len(subs),
        'goals':               goals,
        'by_category':         by_category,
        'budget_by_category':  budget_by_category,
        'expense_count':       len(expenses),
        'income_count':        len(incomes),
    }
def recalculate_all_goals(user_id):
    """
    Phase 7 — Goal delay calculator with allocation awareness.
    Uses allocation_pct to determine monthly savings per goal.
    """
    from app import db

    summary         = get_monthly_summary(user_id)
    monthly_savings = max(0.0, summary['savings'] - summary['sub_cost'])
    goals           = Goal.query.filter_by(user_id=user_id, achieved=False).all()
    insights        = []

    for goal in goals:
        # If allocation set, use that portion; otherwise use equal split
        if goal.allocation_pct > 0:
            goal_savings = round(monthly_savings * (goal.allocation_pct / 100), 2)
        elif len(goals) > 0:
            goal_savings = round(monthly_savings / len(goals), 2)
        else:
            goal_savings = 0.0

        goal.recalculate_eta(goal_savings)
        db.session.commit()

        original = goal.target_months
        new_est  = goal.estimated_months

        if new_est is None:
            insights.append({
                'goal':    goal.name,
                'status':  'no_savings',
                'message': f'"{goal.name}" is at risk — you are not saving enough to reach it.'
            })
        elif new_est > original:
            delay = new_est - original
            insights.append({
                'goal':    goal.name,
                'status':  'delayed',
                'delay':   delay,
                'new_est': new_est,
                'message': f'"{goal.name}" is delayed by {delay} month(s). New estimate: {new_est} months.'
            })
        else:
            insights.append({
                'goal':    goal.name,
                'status':  'on_track',
                'new_est': new_est,
                'message': f'"{goal.name}" is on track — estimated completion in {new_est} months. ✦'
            })

    return insights
def get_savings_forecast(user_id, months=12):
    """
    Phase 11 — Savings forecast.
    Projects savings month by month for the next `months` months
    based on current income, expenses and subscription cost.
    Returns a list of dicts with month label and projected cumulative savings.
    """
    summary         = get_monthly_summary(user_id)
    monthly_savings = max(0.0, summary['savings'] - summary['sub_cost'])

    forecast = []
    cumulative = 0.0
    now = datetime.now()

    for i in range(1, months + 1):
        cumulative = round(cumulative + monthly_savings, 2)
        month_num  = (now.month + i - 1) % 12 + 1
        year       = now.year + ((now.month + i - 1) // 12)
        label      = datetime(year, month_num, 1).strftime('%b %Y')
        forecast.append({
            'month':      label,
            'cumulative': cumulative,
            'monthly':    round(monthly_savings, 2)
        })

    return forecast


def detect_anomalies(user_id):
    """
    Phase 11 — Anomaly detection.
    Flags any expense category where spending this month
    is more than 2 standard deviations above the historical average
    across all previous months on record.
    Falls back to the 240% rule if not enough history.
    """
    from app.models.expense import Expense
    from sqlalchemy import extract, func
    from app import db

    now        = datetime.now()
    anomalies  = []

    # Get all distinct categories the user has expenses in
    categories = db.session.query(Expense.category).filter(
        Expense.user_id == user_id
    ).distinct().all()
    categories = [c[0] for c in categories]

    for category in categories:
        # Sum per month for this category (all history)
        monthly_totals = db.session.query(
            extract('year',  Expense.date).label('yr'),
            extract('month', Expense.date).label('mo'),
            func.sum(Expense.amount_actual).label('total')
        ).filter(
            Expense.user_id  == user_id,
            Expense.category == category
        ).group_by('yr', 'mo').all()

        if len(monthly_totals) < 2:
            # Not enough history — use 240% rule from Phase 6
            continue

        # Current month total
        current_total = next(
            (r.total for r in monthly_totals
             if int(r.yr) == now.year and int(r.mo) == now.month),
            0.0
        )

        # Historical totals excluding current month
        history = [
            r.total for r in monthly_totals
            if not (int(r.yr) == now.year and int(r.mo) == now.month)
        ]

        if not history:
            continue

        mean   = sum(history) / len(history)
        std    = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5

        if std == 0:
            continue

        z_score = (current_total - mean) / std

        if z_score > 2.0:
            pct_above = round(((current_total - mean) / mean) * 100, 1) if mean > 0 else 0
            anomalies.append({
                'type':          'anomaly',
                'category':      category,
                'current':       round(current_total, 2),
                'historical_avg': round(mean, 2),
                'z_score':       round(z_score, 2),
                'pct_above':     pct_above,
                'message':       f'Unusual {category} spending detected — ${current_total:.2f} this month vs avg ${mean:.2f} ({pct_above}% above your norm, z={z_score:.1f}).'
            })

    return anomalies