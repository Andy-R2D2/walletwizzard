# 🧙 WalletWizzard — AI-Powered Personal Finance Intelligence

> *Know exactly where your money goes.*

WalletWizzard is a full-stack web application that helps you track spending, set savings goals, and get a live financial health score — all powered by AI. No spreadsheets, no guesswork.

🔗 **Live app:** https://walletwizzard-production.up.railway.app

---

## 💡 What Problem Do We Solve?

Most people have no idea where their money actually goes at the end of the month. They overspend on food, forget about subscriptions eating into their savings, and never reach their financial goals because they have no system.

WalletWizzard gives you that system — automatically.

- You add your income, set monthly budgets per category, and log expenses
- The app tells you instantly when you're over budget
- AI analyzes your patterns and tells you exactly what to fix
- Your goals update in real time based on your actual savings rate

---

## ✨ Features

### 📊 Smart Budgeting
Set a monthly budget per category (Food, Transport, Entertainment, Health, etc.) — **locked for the entire month** so you can't change your mind mid-month. As you add expenses, a live progress bar shows how much budget remains in real time.

### ❤️ Financial Health Score
A **weighted machine learning model** scores your finances from 0 to 100 based on 6 factors:
- Savings rate
- Spending vs budget
- Subscription load
- Goal progress
- Budget coverage
- Spending consistency

The score updates every time you visit the dashboard.

### 🔮 12-Month Savings Forecast
Based on your current income, expenses, and subscription costs, WalletWizzard projects how much you will have saved 12 months from now — displayed as an interactive line chart.

### 🚨 Anomaly Detection
Using **z-score statistical analysis**, the app detects when your spending in any category is unusually high compared to your own historical average — and alerts you before it becomes a problem.

### 🎯 Savings Goals with Allocation
Create up to 5 savings goals (Car, Emergency Fund, Travel, etc.) and assign a **percentage of your monthly savings** to each one. At the end of the month, click Apply and the amounts are automatically transferred to each goal.

### 🤖 Wizzard AI — Powered by OpenAI GPT-4o
- **Monthly AI summary** — a personalized analysis of what happened this month, what's at risk, and what to do next month
- **Wizzard tips** — short, clever, personalized money tips based on your weakest financial factor
- **Ask Wizzard** — an interactive chat interface where you can ask any question about your finances and get answers grounded in your real data

### 📄 PDF Report Generation
Generate a downloadable **monthly PDF report** containing your full financial snapshot — spending breakdown, health score, goal progress, 12-month forecast, and AI insights — built server-side with **ReportLab** and streamed directly to your browser. No file is ever saved to the server.

### 🔔 Spending Alerts
Real-time alerts when:
- You exceed your category budget
- A subscription costs more than 20% of your income
- Your savings rate drops below 10%
- Unusual spending is detected in any category

---

## 🔒 How We Keep Your Information Secure

Security is built into every layer of WalletWizzard — not added as an afterthought.

### 🔑 Password hashing with bcrypt
Your password is **never stored**. When you register, bcrypt runs your password through a one-way hashing algorithm with a random salt, producing a string like `$2b$12$eImiTXuWVxfM37uY4JANjQ...`. Even if someone accessed the database, they could never reverse it back to your password.

### 🍪 Session cookies signed with HMAC-SHA256
After login, Flask creates an encrypted session cookie in your browser signed with a secret key. If anyone tampers with the cookie to impersonate another user, Flask detects the broken signature and rejects it instantly.

### 🛡️ Route protection with @login_required
Every sensitive page (dashboard, income, expenses, goals, AI) is protected. If you try to access any route without being logged in, you are redirected to the login page before any code runs.

### 💉 SQL injection prevention via SQLAlchemy ORM
We never write raw SQL with user input. Every database query goes through SQLAlchemy, which escapes all values automatically. SQL injection attacks are structurally impossible.

### 👤 Data isolation — user_id on every query
Every single database query filters by `current_user.id`. Even if you are logged in, you cannot access another user's data. Your income, expenses, goals, and budgets are completely invisible to everyone else.

### 🔐 Secrets management with environment variables
API keys, database passwords, and secret keys are **never written in code** and never committed to GitHub. They live in environment variables on Railway, encrypted at rest. Someone cloning this repository gets zero sensitive information.

### 🔒 HTTPS encryption in transit
Railway provides HTTPS automatically. All data between your browser and the server is encrypted. Someone intercepting your network traffic sees only gibberish.

---

## 🏆 Why WalletWizzard?

| Feature | WalletWizzard | Spreadsheet | Basic budget app |
|---|---|---|---|
| AI-powered insights | ✅ | ❌ | ❌ |
| Live health score | ✅ | ❌ | ❌ |
| Anomaly detection | ✅ | ❌ | ❌ |
| PDF reports | ✅ | Manual | ❌ |
| Monthly budget locking | ✅ | ❌ | Rarely |
| Goal allocation | ✅ | ❌ | ❌ |
| Savings forecast | ✅ | Manual | ❌ |
| Fully free to use | ✅ | ✅ | Sometimes |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt |
| Frontend | HTML5, CSS3, JavaScript, Jinja2, Chart.js |
| Database | PostgreSQL (production), SQLite (development) |
| AI / ML | OpenAI GPT-4o-mini, Scikit-Learn, NumPy, Pandas |
| PDF generation | ReportLab |
| Auth | Flask-Login, bcrypt, HMAC-SHA256 |
| Deployment | Railway, Gunicorn, Flask-Migrate |

---

## ❓ FAQ

**Is WalletWizzard free?**
Yes — completely free to use. Create an account and start tracking immediately.

**Is my financial data safe?**
Yes. Your data is stored in an encrypted PostgreSQL database, never shared with third parties, and only accessible to your account. See the security section above for full details.

**Do I need to connect my bank account?**
No. WalletWizzard is manual-entry by design — you control exactly what goes in. No bank connections, no third-party data sharing.

**How does the AI know about my finances?**
When you use the AI features, your financial summary (totals, categories, goals, health score) is sent to OpenAI as context. Your raw transaction details are never sent — only aggregated summaries.

**What happens if I overspend my budget?**
You get an instant alert on the dashboard and when adding the expense. The health score drops, the AI flags it in your monthly summary, and the goal delay calculator updates your savings timeline automatically.

**Can I use WalletWizzard on mobile?**
Yes — the app is fully responsive and works on any browser on any device.

**What is the financial health score?**
It is a number from 0 to 100 calculated by a weighted machine learning model that evaluates your savings rate, spending habits, subscription load, goal progress, budget coverage, and spending consistency.

**How is the 12-month forecast calculated?**
It takes your current monthly savings (income minus expenses minus subscription costs) and projects it forward 12 months. If your savings rate changes month to month, the forecast updates accordingly.

**Can I delete my account and data?**
Yes — contact us and all your data will be permanently removed from the database.

---

## 👨‍💻 Author

Built by **Andy Donghakia Demanou**
B.Sc. Computer Science / Data Science — Ontario Tech University
🔗 [GitHub](https://github.com/Andy-R2D2)

---

*WalletWizzard — Smart finance, simplified. ✦*
