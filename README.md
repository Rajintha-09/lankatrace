# 🚌 LankaTrace — AI-Powered Lost & Found for Sri Lanka Public Transport

> An autonomous AI agent that helps passengers report and recover lost items on Sri Lankan buses and trains — built with Groq LLaMA, Streamlit, semantic matching, and computer vision.

---

## 📌 Problem Statement

Every day, thousands of passengers on Sri Lanka's public transport network lose personal belongings — phones, wallets, bags, IDs — with little to no formal system to recover them. LankaTrace solves this with an intelligent, conversational AI agent that collects reports, analyzes photos, and automatically matches lost items with found ones.

---

## 🎥 Demo Video

▶️ **[Watch on YouTube](#)**  
*(Replace with your YouTube Shorts link)*

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Conversational AI Agent** | Step-by-step chat agent guides users through filing a report using natural language |
| 🧠 **Agent Memory & Planning** | `AgentMemory` class tracks conversation state, collected data, and current step |
| 📷 **AI Image Analysis** | Upload a photo — LLaMA 4 Scout vision model auto-detects item type, color, and features |
| 🔍 **Semantic Matching** | `sentence-transformers` + cosine similarity + rule-based hybrid scoring to match lost ↔ found reports |
| 💬 **AI Match Explanation** | LLaMA 3.3 explains *why* two reports might match in plain English |
| 🗃️ **SQLite Database** | Persistent storage for all reports and matches with auto-generated tracking IDs |
| 📱 **Streamlit UI** | Clean, dark-themed multi-page web app designed for mobile and desktop |
| 🔒 **Ownership Verification** | Lost reporters provide a secret detail to verify identity when collecting items |

---

## 🏗️ Project Architecture

```
lankatrace/
│
├── app.py                  # Main Streamlit entry point (homepage + navigation)
├── agent.py                # Core AI agent — memory, planning, extraction, reasoning
├── matcher.py              # Semantic + hybrid matching engine
├── database.py             # SQLite database — schema, CRUD operations
│
├── pages/
│   ├── 1_report_lost.py    # Lost item reporting page (with photo upload)
│   ├── 2_report_found.py   # Found item reporting page
│   └── 3_my_reports.py     # Track your report by Tracking ID or NIC
│
├── photos/                 # Uploaded item photos (auto-created)
├── lost_found.db           # SQLite database (auto-created on first run)
├── requirements.txt        # Python dependencies
└── .env                    # API keys (NOT uploaded — see setup below)
```

---

## 🧠 How the AI Agent Works

The agent follows a **goal-driven, memory-augmented** architecture:

1. **Goal** — Collect all required details and file a complete report
2. **Plan** — 5-step structured plan (Personal → Item → Incident → Proof → Save & Match)
3. **Memory** — `AgentMemory` class stores conversation history, extracted fields, and current step
4. **Reasoning** — Groq LLaMA 3.3 70B extracts structured data from free-text user replies
5. **Action** — Saves report to SQLite, runs semantic matching, returns results to user

```
User Input → AgentMemory → agent_decide_next_field() → get_question_prompt()
                ↓
         agent_extract() [LLaMA 3.3 70B via Groq]
                ↓
         memory.update() → next turn or → save_report() → run_matching()
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| UI Framework | Streamlit |
| LLM (text) | LLaMA 3.3 70B Versatile via Groq API |
| LLM (vision) | LLaMA 4 Scout 17B via Groq API |
| Semantic Matching | `sentence-transformers` — `all-MiniLM-L6-v2` |
| Similarity | `scikit-learn` cosine similarity |
| Database | SQLite3 (via Python `sqlite3`) |
| Image Processing | Pillow |
| Environment | `python-dotenv` |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/lankatrace.git
cd lankatrace
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key

Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com)

### 4. Run the app
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 🚀 Usage

1. **Report Lost Item** — Chat with the AI agent, optionally upload a photo, and receive a Tracking ID
2. **Report Found Item** — Describe what you found; the agent collects details and checks for matches
3. **Check Your Report** — Enter your Tracking ID or NIC to see your report status and any matches

---

## 📋 Assignment Requirements Checklist

| Requirement | Status |
|---|---|
| Real-world use case | ✅ Sri Lanka public transport lost & found |
| AI agent with reasoning | ✅ Goal-based planning, LLM extraction, decision logic |
| Memory integration | ✅ `AgentMemory` class — full conversation + data state |
| Python with relevant libraries | ✅ Groq, Streamlit, sentence-transformers, Pillow, SQLite |
| Modular, clean code | ✅ Separate modules: agent, matcher, database, pages |
| Interactive user interface | ✅ Streamlit multi-page app |
| YouTube Short demo | ✅ [Link above](#) |

---

## 📄 License

This project was developed as an individual academic assignment for the **Data Science Applications and AI [LB3114]** module at **General Sir John Kotelawala Defence University** — Intake 41, 3rd Year 1st Semester.

---

*Built with ❤️ for Sri Lanka 🇱🇰*
