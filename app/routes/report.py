from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

report_bp = Blueprint('report', __name__)


@report_bp.route('/report')
@login_required
def index():
    return render_template('report/index.html', now=datetime.now())


@report_bp.route('/report/download')
@login_required
def download():
    from app.services.pdf_report import generate_pdf

    # Try to get AI summary — gracefully skip if no API key
    ai_summary = None
    try:
        from app.services.ai_engine import get_monthly_ai_summary
        ai_summary = get_monthly_ai_summary(current_user.id)
    except Exception:
        pass

    try:
        buffer   = generate_pdf(current_user, ai_summary=ai_summary)
        filename = f'walletwizzard_{datetime.now().strftime("%Y_%m")}.pdf'
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Could not generate report: {str(e)}', 'error')
        return redirect(url_for('report.index'))