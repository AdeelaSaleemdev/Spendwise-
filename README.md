💰 SpendWise

A personal finance tracker built with Flask and SQLite, designed to help users log expenses, set budgets, and get AI-powered spending insights — all through a clean, modern web interface.

🔗 Live Demo: adeelasy.pythonanywhere.com

✨ Features
Add / Edit / Delete Expenses — full CRUD functionality with safe delete confirmation
Monthly Summary — category-wise spending breakdown with totals
Budget System — set budgets per category and track usage with over-budget warnings
Search & Filter — filter expenses by category, month, or minimum amount
Dashboard — visual overview with total spent, highest spending category, average daily spend, and a spending bar chart
AI Spending Insights — ask natural-language questions about your spending, powered by Google's Gemini API
Responsive, Styled UI — consistent theme across all pages with custom backgrounds and a modern navbar
🛠️ Tech Stack
Backend: Python, Flask
Database: SQLite
Frontend: HTML, CSS (Jinja2 templating)
AI Integration: Google Gemini API
Deployment: PythonAnywhere
🔒 Security & Code Quality

This project went through a dedicated review pass to fix common beginner pitfalls found in many first Flask apps:

Disabled Flask's debug mode in production (debug=False) to prevent remote code execution risk
Changed the delete route from a GET link to a POST request with a confirmation prompt, so destructive actions can't be triggered accidentally (e.g. by a crawler or link prefetch)
Added input validation on all number fields (amount, budget) to handle missing or invalid input gracefully instead of crashing
Compressed and optimized all background images for faster page loads
🚀 Running Locally
Clone the repo:
bash
   git clone https://github.com/AdeelaSaleemdev/Spendwise-.git
   cd Spendwise-
Install dependencies:
bash
   pip install flask python-dotenv google-generativeai
Create a .env file in the project root with your Gemini API key:
   GEMINI_API_KEY=your_api_key_here
Run the app:
bash
   python main.py
Open your browser at http://127.0.0.1:5000
📌 About This Project

SpendWise was built as a hands-on learning project — starting from a simple command-line, file-based expense tracker and evolving step by step into a fully deployed web application with a database, AI integration, and a security-reviewed codebase. It reflects a "learn by building" approach: refreshing core concepts, then applying them directly to a real, working product.
