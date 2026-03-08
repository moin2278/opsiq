import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

# Connect to (or create) our database
conn = sqlite3.connect('database/opsiq.db')
cursor = conn.cursor()

# ── TABLE 1: incidents ──────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY,
    date TEXT,
    line TEXT,
    station TEXT,
    type TEXT,
    severity TEXT,
    resolved INTEGER,
    resolution_minutes INTEGER
)
''')

# ── TABLE 2: device_health ──────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS device_health (
    id INTEGER PRIMARY KEY,
    date TEXT,
    station TEXT,
    device_type TEXT,
    status TEXT,
    uptime_pct REAL
)
''')

# ── TABLE 3: maintenance ────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY,
    date TEXT,
    station TEXT,
    technician TEXT,
    task TEXT,
    duration_minutes INTEGER,
    completed INTEGER
)
''')

# ── SEED DATA ───────────────────────────────────────────────────
lines     = ['A', '1', 'L', 'N', 'Q', '6', 'F', 'G']
stations  = ['Times Sq', 'Union Sq', 'Atlantic Av', 'Jay St', 'Fulton St',
             'Grand Central', 'Borough Hall', '34th St', 'Canal St', 'Chambers St']
inc_types = ['Signal Failure', 'Door Malfunction', 'Track Issue',
             'Power Outage', 'Elevator Out', 'Escalator Out', 'Flooding']
severities = ['Low', 'Medium', 'High', 'Critical']
devices    = ['Elevator', 'Escalator', 'Turnstile', 'PA System', 'Camera', 'Signal Box']
tasks      = ['Routine Check', 'Part Replacement', 'Software Update',
              'Emergency Repair', 'Inspection', 'Cleaning']
techs      = ['James R.', 'Maria S.', 'Kevin L.', 'Priya M.', 'Omar T.']

random.seed(42)
base_date = datetime(2024, 1, 1)

incidents, device_rows, maintenance_rows = [], [], []

for i in range(500):
    d = base_date + timedelta(days=random.randint(0, 364))
    incidents.append((
        d.strftime('%Y-%m-%d'),
        random.choice(lines),
        random.choice(stations),
        random.choice(inc_types),
        random.choice(severities),
        random.randint(0, 1),
        random.randint(10, 480)
    ))

for i in range(400):
    d = base_date + timedelta(days=random.randint(0, 364))
    device_rows.append((
        d.strftime('%Y-%m-%d'),
        random.choice(stations),
        random.choice(devices),
        random.choice(['Online', 'Offline', 'Degraded']),
        round(random.uniform(60, 100), 2)
    ))

for i in range(300):
    d = base_date + timedelta(days=random.randint(0, 364))
    maintenance_rows.append((
        d.strftime('%Y-%m-%d'),
        random.choice(stations),
        random.choice(techs),
        random.choice(tasks),
        random.randint(30, 300),
        random.randint(0, 1)
    ))

cursor.executemany('INSERT INTO incidents (date,line,station,type,severity,resolved,resolution_minutes) VALUES (?,?,?,?,?,?,?)', incidents)
cursor.executemany('INSERT INTO device_health (date,station,device_type,status,uptime_pct) VALUES (?,?,?,?,?)', device_rows)
cursor.executemany('INSERT INTO maintenance (date,station,technician,task,duration_minutes,completed) VALUES (?,?,?,?,?,?)', maintenance_rows)

conn.commit()
conn.close()

print("✅ Database created with:")
print(f"   • {len(incidents)} incident records")
print(f"   • {len(device_rows)} device health records")
print(f"   • {len(maintenance_rows)} maintenance records")