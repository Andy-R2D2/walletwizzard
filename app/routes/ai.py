from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.services.ai_engine import get_monthly_ai_summary, get_wizzard_tip, ask_wizzard

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai/summary')
@login_required
def summary():
    """Full monthly AI summary page."""
    try:
        ai_summary = get_monthly_ai_summary(current_user.id)
        tip        = get_wizzard_tip(current_user.id)
    except Exception as e:
        ai_summary = f'Could not generate AI summary: {str(e)}'
        tip        = '✦ Add your OpenAI API key to .env to enable AI insights.'

    return render_template('ai/summary.html',
                           ai_summary=ai_summary,
                           tip=tip)


@ai_bp.route('/ai/ask', methods=['POST'])
@login_required
def ask():
    """AJAX endpoint — Wizzard chat."""
    data     = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'answer': 'Please ask a question.'})

    try:
        answer = ask_wizzard(current_user.id, question)
    except Exception as e:
        answer = f'Wizzard is unavailable right now: {str(e)}'

    return jsonify({'answer': answer})


@ai_bp.route('/ai/tip')
@login_required
def tip():
    """Returns a fresh Wizzard tip as JSON — used by dashboard."""
    try:
        t = get_wizzard_tip(current_user.id)
    except Exception as e:
        t = '✦ Add your OpenAI API key to .env to enable Wizzard tips.'
    return jsonify({'tip': t})