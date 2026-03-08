import sqlite3
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DB_PATH = "database/opsiq.db"

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

def get_sql(conversation_history: list, user_question: str) -> str:
    """Convert natural language to SQL — with full conversation context"""

    # 📖 CONCEPT: We pass the entire conversation history to Claude
    # so it understands follow-up questions like "now filter by that station"
    messages = conversation_history + [
        {"role": "user", "content": user_question}
    ]

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SCHEMA,
        messages=messages
    )
    return message.content[0].text.strip()


def run_sql(sql: str) -> list:
    """Execute SQL against the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def explain_results(conversation_history: list, user_question: str, sql: str, results: list) -> str:
    """Explain results in plain English — aware of conversation context"""

    messages = conversation_history + [
        {"role": "user", "content": f"""
Question: {user_question}
SQL Used: {sql}
Results: {results}

Write a clear 2-4 sentence insight. Be specific with numbers.
Reference previous context if this is a follow-up question.
"""}
    ]

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="You are an operations analyst. Give sharp, specific insights. Sound like a smart analyst, not a chatbot.",
        messages=messages
    )
    return message.content[0].text.strip()


def ask(question: str, conversation_history: list) -> dict:
    """Main function — takes question + history, returns result + updated history"""

    # Step 1: Natural language → SQL (with memory)
    sql = get_sql(conversation_history, question)

    # Step 2: Run SQL
    results = run_sql(sql)

    # Step 3: Explain results (with memory)
    insight = explain_results(conversation_history, question, sql, results)

    # 📖 CONCEPT: We append both the question AND answer to history
    # This is how all LLM chat memory works — it's just a growing list
    updated_history = conversation_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": f"SQL: {sql}\nResults: {results}\nInsight: {insight}"}
    ]

    return {
        "question": question,
        "sql": sql,
        "results": results,
        "insight": insight,
        "history": updated_history  # pass this back to the frontend
    }