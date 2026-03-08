# ==============================================================================
# 🏥 SMART CLINIC QUEUE SYSTEM (Offline/Online)
# 👨‍💻 Made by: Lakshay Walia
# ⚙️ Tech Stack: Python (Flask), SQLite, HTML/CSS/JS
# 📌 Description: A contactless queue management system with auto-reset & live sync.
# ==============================================================================
import os
import sqlite3
import socket
import threading
import webbrowser
import uuid
import qrcode
from flask import Flask, request, jsonify, render_template_string, Response

# --- PROMETHEUS IMPORTS ---
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
DB_NAME = 'clinic_DB.db'
PORT = 5000

# ==========================================
# PROMETHEUS METRICS DEFINITIONS
# ==========================================
TOKENS_BOOKED = Counter('clinic_tokens_booked_total', 'Total patient traffic')
QUEUE_RESETS = Counter('clinic_queue_resets_total', 'System session resets')
PATIENTS_CALLED = Counter('clinic_patients_called_total', 'Doctor efficiency/throughput')

# ==========================================
# DATABASE SETUP & HELPER FUNCTIONS
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, token INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Initialize default settings if they don't exist
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('current_token', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('session_id', ?)", (str(uuid.uuid4()),))
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_qr():
    ip = get_local_ip()
    url = f"http://{ip}:{PORT}/patient"
    qr = qrcode.make(url)
    qr.save("clinic_qr.png")
    print(f"\n✅ QR Code generated as 'clinic_qr.png'. Points to: {url}")
    return url

# ==========================================
# FRONTEND TEMPLATES (HTML/CSS/JS)
# ==========================================
BASE_CSS = """
<style>
    :root { --bg: #121212; --card: #1e1e1e; --text: #ffffff; --primary: #3b82f6; --success: #22c55e; --danger: #ef4444; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
    .container { background-color: var(--card); padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 100%; max-width: 400px; text-align: center; }
    h1, h2, h3 { margin-top: 0; }
    input { width: 90%; padding: 12px; margin-bottom: 20px; border-radius: 6px; border: 1px solid #333; background: #2a2a2a; color: white; font-size: 16px; }
    button { width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; color: white; margin-bottom: 10px; }
    button.primary { background-color: var(--primary); }
    button.primary:hover { background-color: #2563eb; }
    button.success { background-color: var(--success); }
    button.danger { background-color: var(--danger); }
    .status-box { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .big-number { font-size: 48px; font-weight: bold; color: var(--primary); margin: 10px 0; }
    .pulse { animation: pulse-green 1.5s infinite; border: 2px solid var(--success); }
    @keyframes pulse-green { 0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(34, 197, 94, 0); } 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); } }
    .patient-list { text-align: left; margin-top: 20px; max-height: 250px; overflow-y: auto; }
    .patient-item { padding: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
    .active-patient { color: var(--success); font-weight: bold; }
</style>
"""

PATIENT_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clinic Queue</title>
    {BASE_CSS}
</head>
<body>
    <div class="container" id="booking-view">
        <h2>🏥 Join the Queue</h2>
        <input type="text" id="patient-name" placeholder="Enter your full name" autocomplete="off">
        <button class="primary" onclick="bookToken()">Get Token</button>
    </div>

    <div class="container" id="status-view" style="display: none;">
        <h2>Your Status</h2>
        <div class="status-box" id="my-status-box">
            <p>Your Token</p>
            <div class="big-number" id="my-token">--</div>
            <p id="turn-message">Please wait...</p>
        </div>
        <div class="status-box">
            <p>Currently Serving</p>
            <div class="big-number" style="color: white; font-size: 32px;" id="current-token">--</div>
            <p id="people-ahead">--</p>
        </div>
    </div>

    <script>
        let myToken = localStorage.getItem('clinic_token');
        let mySession = localStorage.getItem('clinic_session');

        function toggleViews() {{
            document.getElementById('booking-view').style.display = myToken ? 'none' : 'block';
            document.getElementById('status-view').style.display = myToken ? 'block' : 'none';
        }}

        async function bookToken() {{
            const name = document.getElementById('patient-name').value;
            if (!name) return alert("Please enter your name!");
            
            const res = await fetch('/api/book', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{name: name}})
            }});
            const data = await res.json();
            
            myToken = data.token;
            mySession = data.session_id;
            localStorage.setItem('clinic_token', myToken);
            localStorage.setItem('clinic_session', mySession);
            toggleViews();
            pollStatus();
        }}

        async function pollStatus() {{
            if (!myToken) return;
            try {{
                const res = await fetch('/api/status');
                const data = await res.json();
                
                // Auto-Reset Protection Check
                if (data.session_id !== mySession) {{
                    localStorage.removeItem('clinic_token');
                    localStorage.removeItem('clinic_session');
                    myToken = null;
                    mySession = null;
                    alert("The queue was reset by the doctor. Please re-register.");
                    toggleViews();
                    return;
                }}

                document.getElementById('my-token').innerText = "#" + myToken;
                document.getElementById('current-token').innerText = "#" + data.current_token;
                
                let ahead = parseInt(myToken) - parseInt(data.current_token);
                let statusBox = document.getElementById('my-status-box');
                let turnMsg = document.getElementById('turn-message');

                if (ahead > 0) {{
                    document.getElementById('people-ahead').innerText = ahead + " people ahead of you";
                    statusBox.className = "status-box";
                    turnMsg.innerText = "Please wait in the lobby.";
                }} else if (ahead === 0) {{
                    document.getElementById('people-ahead').innerText = "It is your turn!";
                    statusBox.className = "status-box pulse";
                    turnMsg.innerText = "Please proceed to the doctor's cabin.";
                }} else {{
                    document.getElementById('people-ahead').innerText = "Missed / Completed";
                    statusBox.className = "status-box";
                    turnMsg.innerText = "Your turn has passed.";
                }}
            }} catch (e) {{ console.error("Polling error"); }}
        }}

        toggleViews();
        if(myToken) pollStatus();
        setInterval(pollStatus, 2000); // Polls every 2s as per architecture
    </script>
</body>
</html>
"""

DOCTOR_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doctor Dashboard</title>
    {BASE_CSS}
</head>
<body>
    <div class="container" style="max-width: 600px;">
        <h2>👨‍⚕️ Doctor Dashboard</h2>
        
        <div class="status-box">
            <p>Currently Serving</p>
            <div class="big-number" id="current-token">--</div>
        </div>

        <button class="success" onclick="callNext()">🔊 Call Next Patient</button>
        <button class="danger" onclick="resetQueue()">⚠️ Reset Queue</button>

        <div class="patient-list" id="patient-list">
            </div>
    </div>

    <script>
        async function fetchQueue() {{
            const res = await fetch('/api/status');
            const data = await res.json();
            
            document.getElementById('current-token').innerText = "#" + data.current_token;
            
            let listHTML = "<h3>Queue List</h3>";
            if (data.queue.length === 0) listHTML += "<p>No patients in queue.</p>";
            
            data.queue.forEach(p => {{
                let isActive = p.token == data.current_token ? "active-patient" : "";
                let status = p.token < data.current_token ? "(Done)" : "";
                if (p.token == data.current_token) status = "👈 Serving";
                
                listHTML += `<div class="patient-item ${{isActive}}">
                    <span><b>#${{p.token}}</b> ${{p.name}}</span>
                    <span>${{status}}</span>
                </div>`;
            }});
            
            document.getElementById('patient-list').innerHTML = listHTML;
        }}

        async function callNext() {{
            await fetch('/api/next', {{method: 'POST'}});
            fetchQueue();
        }}

        async function resetQueue() {{
            if(confirm("Are you sure? This will wipe the queue and reset all patient screens.")) {{
                await fetch('/api/reset', {{method: 'POST'}});
                fetchQueue();
            }}
        }}

        fetchQueue();
        setInterval(fetchQueue, 2000);
    </script>
</body>
</html>
"""

# ==========================================
# FLASK ROUTES & APIs
# ==========================================

@app.route('/')
def index():
    return "<h1>Smart Clinic QMS</h1><a href='/doctor'>Go to Doctor Dashboard</a> | <a href='/patient'>Go to Patient View</a>"

@app.route('/patient')
def patient_view():
    return render_template_string(PATIENT_HTML)

@app.route('/doctor')
def doctor_view():
    return render_template_string(DOCTOR_HTML)

# --- NEW METRICS ROUTE ---
@app.route('/metrics')
def metrics():
    """Expose metrics to Prometheus"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/api/book', methods=['POST'])
def book_token():
    name = request.json.get('name')
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT MAX(token) FROM patients")
    max_token = c.fetchone()[0]
    next_token = 1 if max_token is None else max_token + 1
    
    c.execute("INSERT INTO patients (name, token) VALUES (?, ?)", (name, next_token))
    
    c.execute("SELECT value FROM settings WHERE key='session_id'")
    session_id = c.fetchone()['value']
    
    conn.commit()
    conn.close()
    
    # TRIGGER SRE METRIC: Patient Booked
    TOKENS_BOOKED.inc() 
    
    return jsonify({"token": next_token, "session_id": session_id})

@app.route('/api/status', methods=['GET'])
def get_status():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT value FROM settings WHERE key='current_token'")
    current_token = int(c.fetchone()['value'])
    
    c.execute("SELECT value FROM settings WHERE key='session_id'")
    session_id = c.fetchone()['value']
    
    c.execute("SELECT * FROM patients ORDER BY token ASC")
    patients = [{"id": row['id'], "name": row['name'], "token": row['token']} for row in c.fetchall()]
    
    conn.close()
    return jsonify({"current_token": current_token, "session_id": session_id, "queue": patients})

@app.route('/api/next', methods=['POST'])
def call_next():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT value FROM settings WHERE key='current_token'")
    current = int(c.fetchone()['value'])
    
    c.execute("SELECT MAX(token) FROM patients")
    max_token = c.fetchone()[0]
    max_token = 0 if max_token is None else max_token
    
    if current < max_token:
        c.execute("UPDATE settings SET value=? WHERE key='current_token'", (str(current + 1),))
        # TRIGGER SRE METRIC: Doctor called next
        PATIENTS_CALLED.inc()
        
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/reset', methods=['POST'])
def reset_queue():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM patients")
    c.execute("DELETE FROM sqlite_sequence WHERE name='patients'") 
    
    c.execute("UPDATE settings SET value='0' WHERE key='current_token'")
    c.execute("UPDATE settings SET value=? WHERE key='session_id'", (str(uuid.uuid4()),))
    
    conn.commit()
    conn.close()
    
    # TRIGGER SRE METRIC: Queue Reset
    QUEUE_RESETS.inc()
    
    return jsonify({"success": True})

# ==========================================
# MAIN EXECUTION
# ==========================================
def open_browser():
    webbrowser.open_new(f'http://127.0.0.1:{PORT}/doctor')

if __name__ == '__main__':
    print("Initializing Database...")
    init_db()
    
    print("Generating Local QR Code...")
    generate_qr()
    
    print("Opening Doctor Dashboard...")
    threading.Timer(1.25, open_browser).start()
    
    app.run(host='0.0.0.0', port=PORT, debug=False)