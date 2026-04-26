# 🧠 Catalyst — AI Skill Assessment & Personalized Learning Plan Agent

> Built for **Deccan AI Catalyst Hackathon 2026** — Solo, 48 hours, zero fluff.

## 🔗 Links

* **Live Demo:** https://catalyst-ai-agent-hmb5dx8s9geistt2c4pv5b.streamlit.app/
* **GitHub:** https://github.com/prateekpatel2877/catalyst-ai-agent
* **Demo Video:** [Coming Soon]

---

## 🎯 Problem Statement

A resume tells you what someone *claims* to know — not how well they actually know it.

This agent takes a Job Description and a candidate's resume, **conversationally assesses real proficiency** on each required skill, identifies gaps, and generates a **personalized learning plan** with curated resources and time estimates.

---

## 🚀 How It Works

Resume (PDF/DOCX) + Job Description
↓
Skill Extractor Agent
→ Extracts required skills from JD
→ Extracts claimed skills from Resume
→ Builds a skill matrix
↓
Conversational Assessment Agent
→ Generates adaptive questions per skill
→ 3 rounds: Conceptual → Practical → Scenario-based
→ Adjusts difficulty based on answers (easy/medium/hard)
→ Scores each answer using LLM as judge (0-10)
↓
Gap Analyzer
→ Identifies critical gaps, moderate gaps, strong skills
→ Finds adjacent skills (easy wins based on existing strengths)
↓
Learning Plan Generator
→ Ordered learning plan with milestones
→ Time estimates per skill
→ Curated resources via semantic search (sentence-transformers)

---

## 🏗️ Architecture

### Tech Stack

| Layer           | Tool                                      |
| --------------- | ----------------------------------------- |
| Frontend        | Streamlit                                 |
| LLM             | Groq API — Llama 3.3 70B Versatile        |
| Resume Parsing  | PyMuPDF + python-docx                     |
| Embeddings      | sentence-transformers (all-MiniLM-L6-v2)  |
| Resource Search | Cosine similarity search (no external DB) |
| Deployment      | Streamlit Community Cloud                 |

### Project Structure

catalyst/
├── app.py                  # Streamlit main app (all stages)
├── agents/
│   ├── skill_extractor.py  # JD + Resume → skill matrix
│   ├── assessor.py         # Adaptive conversational assessment
│   ├── gap_analyzer.py     # Gap detection + adjacency logic
│   └── planner.py          # Learning plan generator
├── utils/
│   ├── resume_parser.py    # PDF/DOCX → clean text
│   ├── chroma_store.py     # Semantic resource retrieval
│   └── scoring.py          # Weighted proficiency scoring
├── prompts/
│   └── templates.py        # All LLM prompt templates
├── data/
│   └── resources.json      # 50+ curated Indian + global learning resources
└── requirements.txt

---

## 🧠 Scoring Logic

Each skill is assessed over **3 adaptive rounds:**

| Round | Type           | Difficulty               |
| ----- | -------------- | ------------------------ |
| 1     | Conceptual     | Starts at Medium         |
| 2     | Practical      | Adjusts based on Round 1 |
| 3     | Scenario-based | Adjusts based on Round 2 |

### Proficiency Score Formula

weighted_score = score × confidence_multiplier × difficulty_weight

Difficulty weights:   easy=0.2, medium=0.5, hard=0.8
Confidence weights:   low=0.7, medium=1.0, high=1.2

Final score = weighted_sum / total_weight (normalized to 0-10)

### Proficiency Labels

| Score     | Label          |
| --------- | -------------- |
| 8.5 - 10  | Expert         |
| 7.0 - 8.4 | Proficient     |
| 5.5 - 6.9 | Intermediate   |
| 3.5 - 5.4 | Beginner       |
| 0 - 3.4   | No Proficiency |

---

## 📊 Gap Analysis Logic

| Category     | Condition   | Action                        |
| ------------ | ----------- | ----------------------------- |
| Critical Gap | Score < 5   | Must learn before applying    |
| Moderate Gap | Score 5–6.9 | Should improve                |
| Strong Skill | Score ≥ 7   | Leverage in adjacent learning |

**Adjacent Skills:** LLM identifies skills the candidate can realistically acquire quickly, based on their existing strengths.

---

## 📚 Resource Retrieval

Learning resources (50+ entries covering Python, ML, NLP, SQL, GenAI, etc.) are embedded using `sentence-transformers/all-MiniLM-L6-v2`. When generating the learning plan, cosine similarity search finds the most semantically relevant resources for each skill gap — not just keyword matching.

Resources include Indian platforms: **NPTEL, GeeksforGeeks, Analytics Vidhya, Scaler, Great Learning** alongside global platforms like Coursera, Hugging Face, fast.ai.

---

## 🛠️ Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/prateekpatel2877/catalyst-ai-agent
cd catalyst-ai-agent
```

### 2. Create environment

```bash
conda create -n catalyst python=3.11 -y
conda activate catalyst
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API key

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your free API key at https://console.groq.com

### 5. Run the app

```bash
streamlit run app.py
```

---

## 📝 Sample Input

**Resume:** Any PDF or DOCX resume

**Job Description:**
We are looking for a Data Scientist with:
Python programming
Machine Learning (Scikit-learn, XGBoost)
SQL and database querying
Data Analysis (Pandas, NumPy)
NLP

---

## 📤 Sample Output

* **Skill Scores:** Python 9.0/10 (Expert), NLP 6.0/10 (Intermediate)
* **Gap Analysis:** NLP identified as moderate gap, adjacent to Machine Learning
* **Learning Plan:** 8 week NLP path — Hugging Face NLP Course, NPTEL NLP, milestones included

---

## 🔑 Tools & APIs Declaration

| Tool                     | Purpose               | Cost              |
| ------------------------ | --------------------- | ----------------- |
| Groq API (Llama 3.3 70B) | LLM inference         | Free tier         |
| sentence-transformers    | Local embeddings      | Free, open source |
| Streamlit                | Frontend + deployment | Free              |
| PyMuPDF                  | PDF parsing           | Free, open source |
| python-docx              | DOCX parsing          | Free, open source |

---

## 👤 Author

**Prateek Patel**

* GitHub: https://github.com/prateekpatel2877
* LinkedIn: https://linkedin.com/in/prateek728
* Email: [prateekpatel2877@gmail.com](mailto:prateekpatel2877@gmail.com)

---

*Built for Deccan AI Catalyst Hackathon 2026 — 48 hours, solo, real working code.*
