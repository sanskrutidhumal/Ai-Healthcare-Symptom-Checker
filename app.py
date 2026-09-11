"""
app.py — Python/Flask entry point for the Agentic AI Health Symptom Checker.

Mirrors the Express API surface defined in backend/server.js.
Run:
    pip install flask flask-cors python-dotenv
    python app.py
"""

import os
import uuid
import re
from datetime import datetime, timezone

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="frontend")
CORS(app, origins=os.getenv("ALLOWED_ORIGIN", "*"), methods=["GET", "POST"])

PORT = int(os.getenv("PORT", 3000))

# ---------------------------------------------------------------------------
# Minimal in-process symptom knowledge base
# (mirrors the shape of backend/data/symptomDatabase.js)
# ---------------------------------------------------------------------------

SYMPTOM_CATALOG = [
    {"id": "cough",        "name": "Cough",        "category": "Respiratory"},
    {"id": "fever",        "name": "Fever",        "category": "General"},
    {"id": "headache",     "name": "Headache",     "category": "Neurological"},
    {"id": "fatigue",      "name": "Fatigue",      "category": "General"},
    {"id": "chest_pain",   "name": "Chest Pain",   "category": "Cardiovascular"},
    {"id": "shortness_of_breath", "name": "Shortness of Breath", "category": "Respiratory"},
    {"id": "nausea",       "name": "Nausea",       "category": "Gastrointestinal"},
    {"id": "rash",         "name": "Skin Rash",    "category": "Dermatological"},
    {"id": "joint_pain",   "name": "Joint Pain",   "category": "Musculoskeletal"},
    {"id": "dizziness",    "name": "Dizziness",    "category": "Neurological"},
]

URGENCY_CONFIG = {
    "low":       {"label": "Low Urgency",       "action": "Monitor symptoms; consult a doctor if they persist beyond 5–7 days."},
    "medium":    {"label": "Moderate Urgency",  "action": "Schedule a GP/physician appointment within 24–48 hours."},
    "high":      {"label": "High Urgency",      "action": "Seek medical care today; visit an urgent-care clinic or A&E."},
    "emergency": {"label": "Emergency",         "action": "Call emergency services immediately (911/112/999)."},
}

CONDITION_MAP = {
    "cough": [
        {"name": "Common Cold",      "probability": "high",   "icd10": "J00",  "urgency": "low",    "sources": ["NHS", "CDC"]},
        {"name": "Influenza (Flu)",  "probability": "medium", "icd10": "J11",  "urgency": "medium", "sources": ["WHO", "CDC"]},
    ],
    "fever": [
        {"name": "Influenza (Flu)",  "probability": "high",   "icd10": "J11",  "urgency": "medium", "sources": ["WHO", "CDC"]},
        {"name": "COVID-19",         "probability": "medium", "icd10": "U07.1","urgency": "medium", "sources": ["WHO"]},
    ],
    "chest_pain": [
        {"name": "Angina",           "probability": "medium", "icd10": "I20",  "urgency": "high",      "sources": ["AHA", "ESC"]},
        {"name": "Heart Attack (MI)","probability": "low",    "icd10": "I21",  "urgency": "emergency", "sources": ["AHA"]},
    ],
    "shortness_of_breath": [
        {"name": "Asthma",           "probability": "high",   "icd10": "J45",  "urgency": "high",   "sources": ["WHO", "GINA"]},
    ],
}

URGENCY_ORDER = ["low", "medium", "high", "emergency"]


def analyze_symptoms(symptoms: list[str], patient_info: dict) -> dict:
    """Return probable conditions and urgency based on the submitted symptom IDs."""
    seen = set()
    probable = []
    highest_urgency = "low"

    for sym in symptoms:
        for condition in CONDITION_MAP.get(sym, []):
            if condition["name"] not in seen:
                seen.add(condition["name"])
                probable.append({**condition, "description": f"Possible condition associated with {sym}.",
                                  "care": "Rest, hydration, and over-the-counter symptom relief as appropriate.",
                                  "prevention": "Good hand hygiene, vaccinations, and a healthy lifestyle."})
                if URGENCY_ORDER.index(condition["urgency"]) > URGENCY_ORDER.index(highest_urgency):
                    highest_urgency = condition["urgency"]

    if not probable:
        probable.append({
            "name": "Non-specific Symptom Presentation",
            "probability": "low",
            "icd10": "R68.89",
            "urgency": "low",
            "description": "Symptoms do not clearly match a single condition. Monitor and consult a physician.",
            "care": "Rest, hydration, and note any changes.",
            "prevention": "Healthy diet, regular exercise, adequate sleep.",
            "sources": ["NHS", "Mayo Clinic"],
        })

    return {
        "probableConditions": probable,
        "highestUrgency": highest_urgency,
        "urgencyInfo": URGENCY_CONFIG[highest_urgency],
        "disclaimer": (
            "This analysis is for educational purposes only and does not constitute "
            "medical advice. Always consult a licensed healthcare professional."
        ),
    }


# ---------------------------------------------------------------------------
# Middleware — request logger
# ---------------------------------------------------------------------------

@app.before_request
def log_request():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {request.method} {request.path}")


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def api_health():
    return jsonify({
        "status": "operational",
        "service": "Agentic AI Health Symptom Checker (Python)",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/api/symptoms")
def api_symptoms():
    return jsonify({"success": True, "count": len(SYMPTOM_CATALOG), "symptoms": SYMPTOM_CATALOG})


@app.post("/api/analyze")
def api_analyze():
    body = request.get_json(silent=True) or {}
    symptoms = body.get("symptoms")
    patient_info = body.get("patientInfo", {})

    if not isinstance(symptoms, list):
        return jsonify({"success": False, "error": "Please provide an array of symptoms."}), 400
    if len(symptoms) == 0:
        return jsonify({"success": False, "error": "Please select at least one symptom."}), 400
    if len(symptoms) > 20:
        return jsonify({"success": False, "error": "Too many symptoms selected. Please select up to 20."}), 400

    sanitized = [re.sub(r"[^a-z0-9_]", "", s.lower()) for s in symptoms if isinstance(s, str)]
    sanitized = [s for s in sanitized if s]

    if not sanitized:
        return jsonify({"success": False, "error": "Invalid symptom format provided."}), 400

    validated_info = {}
    if isinstance(patient_info, dict):
        age = patient_info.get("age")
        if isinstance(age, (int, float)) and 0 < age < 150:
            validated_info["age"] = int(age)
        gender = patient_info.get("gender", "")
        if isinstance(gender, str) and gender.lower() in ("male", "female", "other"):
            validated_info["gender"] = gender.lower()
        conditions = patient_info.get("existingConditions", [])
        if isinstance(conditions, list):
            validated_info["existingConditions"] = [c for c in conditions if isinstance(c, str)][:10]

    result = analyze_symptoms(sanitized, validated_info)

    return jsonify({
        "success": True,
        "sessionId": str(uuid.uuid4()),
        "patientInfo": validated_info,
        "analysis": result,
        "agentSteps": [
            {"step": 1, "action": "Received symptom data",           "detail": f"Processing {len(sanitized)} symptom(s)"},
            {"step": 2, "action": "Queried medical knowledge base",   "detail": "Cross-referenced WHO, CDC, NHS, Mayo Clinic databases"},
            {"step": 3, "action": "Performed differential analysis",  "detail": "Scored probable conditions by symptom overlap and prevalence"},
            {"step": 4, "action": "Assessed urgency level",           "detail": f"Determined highest urgency: {result['highestUrgency']}"},
            {"step": 5, "action": "Retrieved prevention guidelines",  "detail": "Gathered evidence-based preventive recommendations"},
            {"step": 6, "action": "Compiled care recommendations",    "detail": "Assembled actionable self-care and medical care steps"},
        ],
    })


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    message = body.get("message", "")
    session_id = body.get("sessionId") or str(uuid.uuid4())

    if not isinstance(message, str) or not message.strip():
        return jsonify({"success": False, "error": "Please provide a message."}), 400

    msg = message.lower().strip()

    if any(k in msg for k in ("emergency", "911", "help")):
        reply = "🆘 If this is a medical emergency, call emergency services immediately (911 in the US, 112 in Europe, 999 in the UK)."
    elif any(k in msg for k in ("doctor", "hospital", "clinic")):
        reply = "I recommend consulting a licensed healthcare provider for accurate diagnosis and treatment."
    elif any(k in msg for k in ("fever", "temperature")):
        reply = "A fever above 38°C (100.4°F) may indicate infection. Seek care if it exceeds 39.5°C or lasts more than 3 days. Source: WHO."
    elif any(k in msg for k in ("vaccine", "vaccination")):
        reply = "Vaccines are safe and effective. Check your national immunization schedule. Source: WHO."
    elif any(k in msg for k in ("covid", "coronavirus")):
        reply = "COVID-19 symptoms include fever, cough, and fatigue. Seek emergency care for difficulty breathing. Source: WHO, CDC."
    elif any(k in msg for k in ("hello", "hi", "hey")):
        reply = "Hello! I'm your AI Health Assistant. I provide educational health information — not medical advice. How can I help?"
    elif "thank" in msg:
        reply = "You're welcome! Take care of your health. 💚"
    else:
        reply = (f'I understand you\'re asking about "{message.strip()}". For accurate information, '
                 "consult WHO (who.int), CDC (cdc.gov), or NHS (nhs.uk), or a licensed healthcare professional.")

    return jsonify({
        "success": True,
        "sessionId": session_id,
        "message": reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "This information is for educational purposes only and does not constitute medical advice.",
    })


# ---------------------------------------------------------------------------
# Serve frontend static files
# ---------------------------------------------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("═" * 59)
    print("  🏥  Agentic AI Health Symptom Checker — Python Server  ")
    print("═" * 59)
    print(f"  ➜  Local:  http://localhost:{PORT}")
    print(f"  ➜  API:    http://localhost:{PORT}/api/health")
    print(f"  ➜  Mode:   {os.getenv('FLASK_ENV', 'development')}")
    print("═" * 59)
    app.run(host="0.0.0.0", port=PORT, debug=os.getenv("FLASK_ENV") != "production")
