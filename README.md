# Agentic AI Health Symptom Checker 🏥

An intelligent, agentic AI system that analyzes health symptoms and provides **evidence-based probable diagnoses, care recommendations, and preventive advice** — sourced from trusted medical authorities including **WHO, CDC, NHS, NIH, and Mayo Clinic**.

---

## 🌟 Features

- **🤖 Agentic AI Pipeline** — Multi-step reasoning: receive → query knowledge base → differential analysis → urgency assessment → recommendations
- **🩺 10 Symptom Categories** — Respiratory, Cardiovascular, Neurological, Gastrointestinal, Dermatological, Musculoskeletal, and more
- **🚦 4-Level Urgency System** — Low, Medium, High, and Emergency with actionable guidance
- **📚 Verified Medical Sources** — All data sourced from WHO, CDC, NHS, NIH, Mayo Clinic, AHA, ESC Guidelines
- **💬 AI Health Chat** — Conversational assistant for general health questions
- **🔒 Privacy-First** — No data stored, session-based, rate-limited, input-sanitized
- **📱 Responsive Design** — Works on desktop and mobile

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment config
copy .env.example .env

# Start the server
npm start
```

Open **http://localhost:3000** in your browser.

### Development Mode (auto-reload)
```bash
npm run dev
```

---

## 🏗️ Project Structure

```
├── backend/
│   ├── server.js              # Express server + API routes
│   ├── test.js                # API test suite
│   └── data/
│       └── symptomDatabase.js # Medical knowledge base (WHO/CDC/NHS data)
├── frontend/
│   ├── index.html             # Main SPA page
│   ├── styles.css             # Full responsive stylesheet
│   └── app.js                 # Frontend logic + API integration
├── package.json
├── .env.example
└── README.md
```

---

## 🔌 API Reference

### `GET /api/health`
Server health check.

### `GET /api/symptoms`
Returns the list of all available symptoms with categories.

**Response:**
```json
{
  "success": true,
  "count": 10,
  "symptoms": [
    { "id": "cough", "name": "Cough", "category": "Respiratory" },
    ...
  ]
}
```

### `POST /api/analyze`
Core analysis endpoint — returns probable conditions, urgency level, care and prevention recommendations.

**Request:**
```json
{
  "symptoms": ["cough", "fever", "headache"],
  "patientInfo": {
    "age": 35,
    "gender": "female",
    "existingConditions": ["asthma"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "uuid",
  "analysis": {
    "probableConditions": [
      {
        "name": "Influenza (Flu)",
        "probability": "medium",
        "icd10": "J11",
        "description": "...",
        "urgency": "medium",
        "care": "...",
        "prevention": "...",
        "sources": ["WHO", "CDC"]
      }
    ],
    "highestUrgency": "medium",
    "urgencyInfo": { "label": "Moderate Urgency", "action": "..." },
    "disclaimer": "..."
  }
}
```

### `POST /api/chat`
AI health chat endpoint for general questions.

**Request:**
```json
{ "message": "What causes fever?", "sessionId": "optional-uuid" }
```

---

## 🧪 Running Tests

Start the server first, then in a new terminal:
```bash
npm test
```

---

## ⚕️ Medical Disclaimer

> This application provides general health information **for educational purposes only**. It does **not** constitute medical advice, diagnosis, or treatment. Always consult a licensed healthcare professional for medical decisions.
>
> **In a medical emergency, call 911 (US) · 112 (EU) · 999 (UK) immediately.**

---

## 📚 Data Sources

All medical content is based on guidelines from:
- [World Health Organization (WHO)](https://www.who.int)
- [Centers for Disease Control (CDC)](https://www.cdc.gov)
- [National Institutes of Health (NIH)](https://www.nih.gov)
- [NHS (UK National Health Service)](https://www.nhs.uk)
- [Mayo Clinic](https://www.mayoclinic.org)
- [American Heart Association (AHA)](https://www.heart.org)
- [European Society of Cardiology (ESC)](https://www.escardio.org)
- [American College of Rheumatology (ACR)](https://www.rheumatology.org)
