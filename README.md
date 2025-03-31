# 🕓 Temporal Robustness Benchmarking of LLMs

This repository contains our custom benchmarking framework designed to test and evaluate the temporal reasoning abilities of Large Language Models (LLMs) like GPT-4, Gemini, and LLaMA.

> ❗ Unlike standard benchmarks like ComplexTempQA, our goal is to go beyond timestamp recall and assess temporal consistency, multi-hop reasoning, and robustness against contradictions.

---

## 📌 Project Goals

- Evaluate how well LLMs handle:
  - Temporal ordering
  - Overlapping and parallel events
  - Indirect durations and counterfactuals
  - Temporal contradictions and hallucinations
- Stress test models using narrative-style fact sets that conflict with real-world timelines.
- Analyze failure modes such as:
  - Memorization bias
  - Confusion in ambiguous ranges (e.g., "early 1980s")
  - Logical inconsistency across question types

---

## 🚀 Benchmark Tool Features

🧠 Built with Streamlit, our interactive tool supports:

- 🧪 Multi-model testing: GPT-4, Gemini, LLaMA (Groq), Claude
- 💬 Multiple question formats:
  - Yes/No
  - Event Order
  - Duration & Range
  - Contradiction Detection
  - Fill-in-the-blank
- 🔍 Annotation + tagging of model failures (hallucination, contradiction, etc.)
- 📊 Logging of responses, verdicts, and error patterns
- 📁 Structured test cases in JSON with:
  - System prompt
  - Synthetic fact set
  - 10–20 question variants

---

## 📂 Repo Structure

📦 Temporal-Robustness-Benchmarking-LLMs/
├── streamlit_app/             # Frontend interface for model testing
│   ├── app.py
│   ├── utils/
│   └── prompts/
├── testcases/                 # JSON files with synthetic fact sets & questions
├── results/                   # CSV logs of model responses and verdicts
├── analysis/                  # Scripts for error heatmaps and aggregation
├── README.md
└── requirements.txt
