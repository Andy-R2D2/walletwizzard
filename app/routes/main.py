from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('welcome.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    from app.services.rules        import run_all_insights, get_monthly_summary, get_savings_forecast
    from app.services.health_score import compute_health_score

    alerts, goal_insights = run_all_insights(current_user.id)
    summary               = get_monthly_summary(current_user.id)
    health                = compute_health_score(current_user.id)
    forecast              = get_savings_forecast(current_user.id, months=12)

    return render_template('dashboard.html',
                           user=current_user,
                           alerts=alerts,
                           goal_insights=goal_insights,
                           summary=summary,
                           health=health,
                           forecast=forecast,
                           planned_by_category=summary['budget_by_category'],
                           now=datetime.now())