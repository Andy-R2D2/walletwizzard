import os
from openai import OpenAI
from app.services.rules        import get_monthly_summary, get_savings_forecast
from app.services.health_score import compute_health_score

def get_client():
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise ValueError('OPENAI_API_KEY is not set.')
    return OpenAI(api_key=key)


def build_context(user_id):
    """
    Builds a structured financial context string from the user's
    real data — passed to OpenAI as the system prompt context.
    """
    summary  = get_monthly_summary(user_id)
    health   = compute_health_score(user_id)
    forecast = get_savings_forecast(user_id, months=12)

    goals_text = ''
    for g in summary['goals']:
        goals_text += (
            f"  - {g.name}: target ${g.target_amount:.2f}, "
            f"saved ${g.saved_amount:.2f} ({g.progress_pct}%), "
            f"allocation {g.allocation_pct:.0f}%, "
            f"estimated {g.estimated_months or '?'} months remaining\n"
        )

    budget_text = ''
    for cat, planned in summary['budget_by_category'].items():
        actual = summary['by_category'].get(cat, 0)
        over   = '⚠ OVER' if actual > planned else '✓ OK'
        budget_text += f"  - {cat}: planned ${planned:.2f}, spent ${actual:.2f} {over}\n"

    context = f"""
USER FINANCIAL SNAPSHOT — {os.getenv('APP_MONTH', 'current month')}

INCOME & EXPENSES:
  Monthly income:    ${summary['total_income']:.2f}
  Total expenses:    ${summary['total_expense']:.2f}
  Total budgeted:    ${summary['total_planned']:.2f}
  Monthly savings:   ${summary['savings']:.2f}
  Savings rate:      {summary['savings_rate']}%
  Subscription cost: ${summary['sub_cost']:.2f}/mo ({summary['sub_count']} active)

BUDGET BY CATEGORY:
{budget_text if budget_text else '  No budgets set yet.'}

SAVINGS GOALS:
{goals_text if goals_text else '  No active goals.'}

FINANCIAL HEALTH SCORE: {health['score']}/100 ({health['label']})
  Factor breakdown:
  - Savings rate score:      {health['breakdown']['savings']}/100
  - Spending vs budget:      {health['breakdown']['spending']}/100
  - Subscription load:       {health['breakdown']['subs']}/100
  - Goal progress:           {health['breakdown']['goals']}/100
  - Budget coverage:         {health['breakdown']['coverage']}/100
  - Spending consistency:    {health['breakdown']['consistency']}/100

12-MONTH FORECAST:
  Projected savings in 12 months: ${forecast[-1]['cumulative']:.2f}
  Monthly savings rate: ${forecast[0]['monthly']:.2f}/mo
"""
    return context


def get_monthly_ai_summary(user_id):
    """
    Generates a full monthly AI summary combining:
    - What happened this month
    - What's at risk
    - What to do next month
    - Wizzard tip
    """
    context = build_context(user_id)

    prompt = f"""
You are WalletWizzard, a friendly but sharp personal finance AI advisor.
You speak directly, warmly, and concisely — no fluff, no filler.
You never say "I" — you address the user as "you".
You always end with a short ✦ Wizzard Tip.

Here is the user's financial data:
{context}

Write a monthly financial summary with these 4 sections:
1. 📊 This month — what happened (2-3 sentences)
2. ⚠ Watch out — biggest risk or problem (1-2 sentences)
3. 🎯 Next month — one concrete action to improve (1-2 sentences)
4. ✦ Wizzard Tip — one short clever money tip personalized to their data

Keep the whole response under 180 words. Be specific with numbers from their data.
"""

    response = get_client().chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are WalletWizzard, a concise and friendly personal finance AI.'},
            {'role': 'user',   'content': prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


def get_wizzard_tip(user_id):
    """
    Generates a single short Wizzard tip for the sidebar.
    Personalized to the user's worst factor.
    """
    health  = compute_health_score(user_id)
    summary = get_monthly_summary(user_id)

    # Find the worst factor
    worst = min(health['factors'], key=lambda f: f['score'])

    prompt = f"""
You are WalletWizzard. Give ONE short, clever, personalized money tip (max 25 words).
Focus on this weak area: {worst['name']} (score: {worst['score']}/100).
Context: {worst['note']}.
Start with ✦ and speak directly to the user.
No hashtags, no emojis except ✦.
"""

    response = get_client().chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=60,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()


def ask_wizzard(user_id, question):
    """
    Answers a specific question from the user about their finances.
    Used by the chat interface.
    """
    context = build_context(user_id)

    prompt = f"""
You are WalletWizzard, a friendly personal finance AI.
You have access to the user's real financial data below.
Answer their question concisely and specifically using their numbers.
Never make up data — only use what's provided.
Keep your answer under 120 words.

USER FINANCIAL DATA:
{context}

USER QUESTION: {question}
"""

    response = get_client().chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are WalletWizzard, a concise personal finance AI advisor.'},
            {'role': 'user',   'content': prompt}
        ],
        max_tokens=200,
        temperature=0.6
    )

    return response.choices[0].message.content.strip()