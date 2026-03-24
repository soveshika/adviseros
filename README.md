# AdviserOS 🤖💼

> **AI-powered financial advisory platform** — built for real-world use with a UK-based financial adviser (40 years of experience).

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?logo=postgresql)
![Claude AI](https://img.shields.io/badge/Claude-Anthropic%20API-orange)
![Status](https://img.shields.io/badge/Status-Live%20Demo-brightgreen)

---

## 📌 Overview

AdviserOS is a full-stack SaaS-style platform that automates the financial advisory workflow. It collects client data through a guided onboarding process, runs an AI analysis of the client's financial situation, and generates a professional PDF suitability report — all in one seamless experience.

Built as a real-world portfolio project in collaboration with an active UK financial adviser, this platform reflects genuine industry requirements rather than a toy demo.

---

## ✨ Features

- **5-Step Onboarding Wizard** — guided client data collection covering personal details, financial goals, risk tolerance, existing assets, and investment preferences
- **AI Analysis Engine** — powered by the Anthropic Claude API to analyse client profiles and generate personalised financial insights
- **PDF Suitability Report Generator** — automated report generation using ReportLab, producing professional-grade documents ready for client delivery
- **SaaS-style Dashboard** — adviser-facing dashboard to manage clients, view reports, and track onboarding status
- **RESTful API** — FastAPI backend with full CRUD operations and structured endpoints
- **PostgreSQL Database** — persistent storage for client profiles, reports, and session data

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, PostgreSQL |
| **Frontend** | React, JavaScript |
| **AI Engine** | Anthropic Claude API |
| **PDF Generation** | ReportLab |
| **Database ORM** | SQLAlchemy |
| **Version Control** | Git / GitHub |

---

## 📁 Project Structure

```
adviseros/
├── adviseros/              # FastAPI backend
│   ├── main.py             # API entry point
│   ├── models/             # Database models
│   ├── routes/             # API routes
│   └── services/           # Business logic
├── adviseros-frontend/     # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Onboarding wizard steps & dashboard
│   │   └── api/            # API service layer
├── ai engine/              # AI analysis logic
│   └── analyser.py         # Claude API integration
└── start-adviseros.sh      # Script to run the full stack locally
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Anthropic API key

### Installation

**1. Clone the repo**
```bash
git clone https://github.com/soveshika/adviseros.git
cd adviseros
```

**2. Set up the backend**
```bash
cd adviseros
pip install -r requirements.txt
cp .env.example .env  # Add your DB credentials and Anthropic API key
uvicorn main:app --reload
```

**3. Set up the frontend**
```bash
cd adviseros-frontend
npm install
npm start
```

**4. Or run everything at once**
```bash
chmod +x start-adviseros.sh
./start-adviseros.sh
```

---

## 📸 Demo

> Live demo available upon request — contact via GitHub or LinkedIn.

---

## 🎯 Why I Built This

I'm transitioning from a Civil Engineering and Business Management background into AI Engineering. AdviserOS is my flagship portfolio project — demonstrating that I can build production-grade, full-stack AI applications that solve real business problems.

The platform was built in response to a real brief from a UK financial adviser with 40 years of experience, making it far more than just a coding exercise.

---

## 👤 Author

**Sonu** — AI Engineer in Training  
📍 London, UK  
🔗 [GitHub: soveshika](https://github.com/soveshika)

---

## 📄 Licence

This project is licensed under the MIT Licence.
