from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.budget  import Budget
from app.models.expense import EXPENSE_CATEGORIES
from app.models.income  import Income
from sqlalchemy import extract
from datetime import datetime

budget_bp = Blueprint('budget', __name__)


def current_month_income(user_id):
    now = datetime.now()
    total = db.session.query(db.func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == now.month,
        extract('year',  Income.date) == now.year
    ).scalar()
    return total or 0.0


@budget_bp.route('/budget')
@login_required
def index():
    now     = datetime.now()
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=now.month,
        year=now.year
    ).all()

    # Build a dict for quick lookup: category -> budget
    budget_map = {b.category: b for b in budgets}

    # Categories not yet budgeted this month
    set_categories = set(budget_map.keys())
    all_categories = EXPENSE_CATEGORIES
    monthly_income = current_month_income(current_user.id)

    return render_template('budget/index.html',
                           budgets=budgets,
                           budget_map=budget_map,
                           all_categories=all_categories,
                           set_categories=set_categories,
                           monthly_income=monthly_income,
                           now=now)


@budget_bp.route('/budget/set/<string:category>', methods=['GET', 'POST'])
@login_required
def set_budget(category):
    now = datetime.now()

    # Validate category
    from app.models.expense import CATEGORY_NAMES
    if category not in CATEGORY_NAMES:
        flash('Invalid category.', 'error')
        return redirect(url_for('budget.index'))

    # Check if already set this month — locked
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category=category,
        month=now.month,
        year=now.year
    ).first()

    if existing:
        flash(f'Budget for {category} is already set for this month and cannot be changed until next month.', 'error')
        return redirect(url_for('budget.index'))

    if request.method == 'POST':
        planned = request.form.get('planned', '').strip()

        try:
            planned = float(planned)
            if planned <= 0:
                raise ValueError
        except ValueError:
            flash('Please enter a valid positive amount.', 'error')
            return render_template('budget/set.html', category=category, now=now)

        # High budget warning — if category budget > 40% of monthly income
        monthly_income = current_month_income(current_user.id)
        if monthly_income > 0 and planned > (monthly_income * 0.40):
            pct = round((planned / monthly_income) * 100, 1)
            flash(f'⚠ Warning: your {category} budget (${planned:.2f}) is {pct}% of your monthly income. Consider reducing it.', 'error')

        budget = Budget(
            user_id=current_user.id,
            category=category,
            planned=planned,
            month=now.month,
            year=now.year
        )
        db.session.add(budget)
        db.session.commit()
        flash(f'{category} budget set to ${planned:.2f} for {now.strftime("%B %Y")}. This cannot be changed until next month.', 'success')
        return redirect(url_for('budget.index'))

    return render_template('budget/set.html', category=category, now=now)