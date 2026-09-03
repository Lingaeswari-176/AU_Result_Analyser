# 🎓 Anna University Result Analyzer

> Upload any Anna University result PDF — get instant SGPA, rank list, arrear analysis, and downloadable PDF reports.

---

## 🚀 Run in 2 Steps

```bash
# Step 1 — Install
pip install streamlit pdfplumber pandas reportlab

# Step 2 — Run
streamlit run app.py
```

Opens at **http://localhost:8501** ✅

---

## ✨ Features

| Feature | Details |
|---|---|
| 📄 PDF Parser | Detects all semesters automatically |
| 🔍 Student Search | Search by register number |
| 📊 Class Analysis | Pass%, arrear%, absent% |
| 📋 Rank List | SGPA-based ranking |
| 📚 Subject-wise | Per-subject pass/fail/arrear stats |
| 🚨 Arrear Analysis | Lists all arrear students |
| ⚙️ Credit Config | Enter credits in sidebar |
| 📥 PDF Report | Download complete analysis |

---

## 📁 Structure

```
au-result-analyzer/
├── app.py              ← Main Streamlit app
├── requirements.txt
├── src/
│   ├── parser.py       ← PDF parsing + semester detection
│   ├── analytics.py    ← SGPA, arrears, class analysis
│   └── report.py       ← PDF report generation
└── .streamlit/
    └── config.toml     ← Light theme config
```

---

## ⚙️ How to Use

1. Upload result PDF in sidebar
2. Enter subject credits (Code|Name|Credits per line)
3. Select semester
4. Navigate tabs: Class Analysis → Search → Rank List → Subject-wise → Arrear → Download

---

## 👩‍💻 Built By

Lingaeswari Kathirvel | Jeppiaar Engineering College | github.com/Lingaeswari-176
