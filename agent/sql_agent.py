import sqlite3
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DB_PATH = "database/opsiq.db"

# ── STEP 1: Tell Claude what our database looks like ────────────
SCHEMA = """
You are an expert SQL assistant for a transit operations database.

Tables:
1. incidents(id, date, line, station, type, severity, resolved, resolution_minutes)
   - line: subway line (A, 1, L, N, Q, 6, F, G)
   - type: Signal Failure, Door Malfunction, Track Issue, Power Outage, Elevator Out, Escalator Out, Flooding
   - severity: Low, Medium, High, Critical
   - resolved: 1=yes, 0=no
   - resolution_minutes: how long to fix

2. device_health(id, date, station, device_type, status, uptime_pct)
   - device_type: Elevator, Escalator, Turnstile, PA System, Camera, Signal Box
   - status: Online, Offline, Degraded
   - uptime_pct: 0-100

3. maintenance(id, date, station, technician, task, duration_minutes, completed)
   - task: Routine Check, Part Replacement, Software Update, Emergency Repair, Inspection, Cleaning
   - completed: 1=yes, 0=no

Rules:
- Return ONLY the raw SQL query, nothing else
- No markdown, no backticks, no explanation
- Use proper SQLite syntax
- Always LIMIT to 20 rows unless asked for totals/counts
"""

def get_schema_and_question(user_question: str) -> str:
    """STEP 1 — Convert natural language to SQL using Claude"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SCHEMA,
        messages=[
            {"role": "user", "content": user_question}
        ]
    )
    
    sql = message.content[0].text.strip()
    return sql


def run_sql(sql: str) -> list:
    """STEP 2 — Execute the SQL against our real database"""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    cursor = conn.cursor()
    
    cursor.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return rows


def explain_results(user_question: str, sql: str, results: list) -> str:
    """STEP 3 — Claude explains the results in plain English"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="You are an operations analyst. Given a question, the SQL used, and the results, write a clear 2-4 sentence insight. Be specific with numbers. Sound like a smart analyst, not a chatbot.",
        messages=[
            {"role": "user", "content": f"""
Question: {user_question}

SQL Used: {sql}

Results: {results}

Write your insight:
"""}
        ]
    )
    
    return message.content[0].text.strip()


def ask(question: str) -> dict:
    """The main function — ties all 3 steps together"""
    
    print(f"\n🔍 Question: {question}")
    
    # Step 1: Natural language → SQL
    sql = get_schema_and_question(question)
    print(f"📝 SQL Generated:\n{sql}")
    
    # Step 2: Run SQL
    results = run_sql(sql)
    print(f"📊 Rows returned: {len(results)}")
    
    # Step 3: Explain results
    insight = explain_results(question, sql, results)
    print(f"💡 Insight:\n{insight}")
    
    return {
        "question": question,
        "sql": sql,
        "results": results,
        "insight": insight
    }


# ── TEST IT ─────────────────────────────────────────────────────
if __name__ == "__main__":
    ask("What are the most common incident types?")
    ask("Which station has the most unresolved incidents?")
    ask("What is the average resolution time for critical incidents?")