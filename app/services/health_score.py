import numpy as np
from app.models.goal import Goal
from app.models.budget import Budget
from app.models.subscription import Subscription
from app.services.rules import get_monthly_summary
from datetime import datetime


def compute_health_score(user_id):
    """
    Weighted scoring model — 6 factors, each scored 0-100.
    Final score = weighted average, rounded to nearest int.

    Factors & weights (total = 100%):
      1. Savings rate          — 30%
      2. Spending vs budget    — 25%
      3. Subscription load     — 15%
      4. Goal progress         — 15%
      5. Budget coverage       — 10%
      6. Spending consistency  — 5%
    """
    summary = get_monthly_summary(user_id)
    now     = datetime.now()

    # ── 1. Savings rate (0-100) ──────────────────────────
    # 20%+ savings rate = 100, 0% = 0, negative = 0
    savings_rate  = max(0.0, summary['savings_rate'])
    savings_score = min(100.0, (savings_rate / 20.0) * 100)

    # ── 2. Spending vs budget (0-100) ────────────────────
    # For each category that has a budget, check if within plan
    budget_by_cat  = summary['budget_by_category']
    actual_by_cat  = summary['by_category']
    total_planned  = sum(budget_by_cat.values())
    total_actual   = sum(actual_by_cat.get(c, 0) for c in budget_by_cat)

    if total_planned > 0:
        ratio          = total_actual / total_planned
        # ratio <= 1 = perfect, ratio = 1.5 = 50% over = 0
        spending_score = max(0.0, min(100.0, (1 - max(0, ratio - 1)) * 100))
    else:
        spending_score = 50.0   # neutral if no budgets set yet

    # ── 3. Subscription load (0-100) ─────────────────────
    # sub_cost / income — ideal < 10%, bad > 30%
    income   = summary['total_income']
    sub_cost = summary['sub_cost']

    if income > 0:
        sub_ratio  = sub_cost / income
        # 0% = 100, 10% = 100, 30%+ = 0
        sub_score  = max(0.0, min(100.0, (1 - max(0, (sub_ratio - 0.10) / 0.20)) * 100))
    else:
        sub_score = 50.0

    # ── 4. Goal progress (0-100) ──────────────────────────
    # Average progress_pct across all active goals
    goals = Goal.query.filter_by(user_id=user_id, achieved=False).all()
    if goals:
        avg_progress  = sum(g.progress_pct for g in goals) / len(goals)
        goal_score    = min(100.0, avg_progress)
    else:
        goal_score    = 50.0   # neutral if no goals

    # ── 5. Budget coverage (0-100) ────────────────────────
    # How many of the 9 categories have a budget set this month?
    budgets_set    = Budget.query.filter_by(
        user_id=user_id,
        month=now.month,
        year=now.year
    ).count()
    coverage_score = min(100.0, (budgets_set / 9) * 100)

    # ── 6. Spending consistency (0-100) ───────────────────
    # Compare this month's expense count vs last month
    # More consistent spending = higher score
    from app.models.expense import Expense
    from sqlalchemy import extract

    last_month = now.month - 1 if now.month > 1 else 12
    last_year  = now.year if now.month > 1 else now.year - 1

    this_count = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == now.month,
        extract('year',  Expense.date) == now.year
    ).count()

    last_count = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == last_month,
        extract('year',  Expense.date) == last_year
    ).count()

    if last_count > 0:
        consistency    = 1 - abs(this_count - last_count) / max(this_count, last_count)
        consistency_score = max(0.0, min(100.0, consistency * 100))
    else:
        consistency_score = 50.0

    # ── Weighted final score ──────────────────────────────
    weights = {
        'savings':     0.30,
        'spending':    0.25,
        'subs':        0.15,
        'goals':       0.15,
        'coverage':    0.10,
        'consistency': 0.05,
    }

    raw_score = (
        savings_score     * weights['savings']     +
        spending_score    * weights['spending']    +
        sub_score         * weights['subs']        +
        goal_score        * weights['goals']       +
        coverage_score    * weights['coverage']    +
        consistency_score * weights['consistency']
    )

    final_score = round(raw_score)

    # ── Label ─────────────────────────────────────────────
    if final_score >= 80:
        label = 'Excellent'
        color = '#63D9B4'
    elif final_score >= 60:
        label = 'Good'
        color = '#63D9B4'
    elif final_score >= 40:
        label = 'Fair'
        color = '#FCD34D'
    else:
        label = 'At risk'
        color = '#FCA5A5'

    # ── Factor breakdown for dashboard display ────────────
    factors = [
        {
            'name':  'Savings rate',
            'score': round(savings_score),
            'pct':   savings_rate,
            'note':  f'{savings_rate:.1f}% savings rate (target: 20%+)'
        },
        {
            'name':  'Spending vs budget',
            'score': round(spending_score),
            'pct':   round(total_actual / total_planned * 100, 1) if total_planned > 0 else 0,
            'note':  f'${total_actual:.0f} spent of ${total_planned:.0f} budgeted'
        },
        {
            'name':  'Subscription load',
            'score': round(sub_score),
            'pct':   round(sub_cost / income * 100, 1) if income > 0 else 0,
            'note':  f'${sub_cost:.0f}/mo in subscriptions ({round(sub_cost/income*100,1) if income > 0 else 0}% of income)'
        },
        {
            'name':  'Goal progress',
            'score': round(goal_score),
            'pct':   round(goal_score),
            'note':  f'{len(goals)} active goal(s), avg {goal_score:.0f}% complete'
        },
        {
            'name':  'Budget coverage',
            'score': round(coverage_score),
            'pct':   round(coverage_score),
            'note':  f'{budgets_set} of 9 categories budgeted'
        },
        {
            'name':  'Consistency',
            'score': round(consistency_score),
            'pct':   round(consistency_score),
            'note':  f'{this_count} expense(s) this month vs {last_count} last month'
        },
    ]

    return {
        'score':   final_score,
        'label':   label,
        'color':   color,
        'factors': factors,
        'breakdown': {
            'savings':     round(savings_score),
            'spending':    round(spending_score),
            'subs':        round(sub_score),
            'goals':       round(goal_score),
            'coverage':    round(coverage_score),
            'consistency': round(consistency_score),
        }
    }