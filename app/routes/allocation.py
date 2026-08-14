from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.goal import Goal
from app.services.rules import get_monthly_summary

allocation_bp = Blueprint('allocation', __name__)


@allocation_bp.route('/allocation', methods=['GET', 'POST'])
@login_required
def index():
    goals   = Goal.query.filter_by(
        user_id=current_user.id,
        achieved=False
    ).all()
    summary = get_monthly_summary(current_user.id)
    monthly_savings = max(0.0, summary['savings'] - summary['sub_cost'])

    if request.method == 'POST':
        total_pct = 0.0
        new_allocs = {}

        for goal in goals:
            key = f'alloc_{goal.id}'
            val = request.form.get(key, '0').strip()
            try:
                pct = float(val)
                if pct < 0:
                    raise ValueError
            except ValueError:
                flash(f'Invalid percentage for "{goal.name}".', 'error')
                return render_template('allocation/index.html',
                                       goals=goals,
                                       monthly_savings=monthly_savings,
                                       summary=summary)
            new_allocs[goal.id] = pct
            total_pct += pct

        if total_pct > 100:
            flash(f'Total allocation is {total_pct:.1f}% — cannot exceed 100%. Please adjust.', 'error')
            return render_template('allocation/index.html',
                                   goals=goals,
                                   monthly_savings=monthly_savings,
                                   summary=summary)

        # Save allocations
        for goal in goals:
            goal.allocation_pct = new_allocs[goal.id]
        db.session.commit()

        unallocated = round(100 - total_pct, 1)
        if unallocated > 0:
            flash(f'Allocations saved. {unallocated}% of your savings (${monthly_savings * unallocated / 100:.2f}) is unallocated — it stays as free cash.', 'success')
        else:
            flash('Allocations saved — 100% of your savings is assigned to goals. ✦', 'success')

        return redirect(url_for('allocation.index'))

    return render_template('allocation/index.html',
                           goals=goals,
                           monthly_savings=monthly_savings,
                           summary=summary)


@allocation_bp.route('/allocation/apply', methods=['POST'])
@login_required
def apply():
    """
    Manually apply this month's allocation to each goal's saved_amount.
    User clicks this once per month to confirm the transfer.
    """
    goals   = Goal.query.filter_by(
        user_id=current_user.id,
        achieved=False
    ).all()
    summary = get_monthly_summary(current_user.id)
    monthly_savings = max(0.0, summary['savings'] - summary['sub_cost'])

    if monthly_savings <= 0:
        flash('No savings to allocate this month.', 'error')
        return redirect(url_for('allocation.index'))

    total_applied = 0.0
    for goal in goals:
        if goal.allocation_pct > 0:
            amount = round(monthly_savings * (goal.allocation_pct / 100), 2)
            goal.saved_amount = round(goal.saved_amount + amount, 2)
            total_applied += amount

            # Mark as achieved if target reached
            if goal.saved_amount >= goal.target_amount:
                goal.achieved = True
                flash(f'🎉 Goal "{goal.name}" achieved!', 'success')

    db.session.commit()
    flash(f'${total_applied:.2f} distributed across your goals based on your allocation. ✦', 'success')
    return redirect(url_for('allocation.index'))