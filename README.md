# 🎹 Performance Insight

A web-based analysis tool that helps classical musicians understand how their tempo and dynamics compare to a professional reference recording.

---

## Overview

Many classical music students can play all the correct notes of a piece, yet the performance still feels unstable or unpolished. The issue is rarely accuracy — it's tempo control, pacing, and dynamic shaping.

Performance Insight turns subjective musical feedback into measurable data.

By analyzing audio recordings and visualizing tempo and loudness over time, this tool helps musicians see *where* their performance diverges and *how* it differs from a reference interpretation.

---

## Problem

Classical interpretation depends heavily on:

- Controlled tempo variation (rubato)
- Dynamic contrast
- Phrase pacing

These are difficult to diagnose by ear alone. Students often struggle to identify:

- Where tempo becomes unstable
- Whether rubato is intentional or inconsistent
- Why certain passages feel rushed or dragged
- How their dynamics compare to professional recordings

Traditional feedback is subjective and limited to lesson time.

---

## Solution

This project analyzes and compares classical recordings using:

- **Tempo extraction (BPM over time)**
- **Dynamic (loudness) curve analysis**
- **DTW-based alignment** to synchronize student and reference performances
- **Time-series visualization**
- **Automated performance insights**

The system aligns two recordings using Dynamic Time Warping (DTW), then computes:

- Mean tempo deviation (aligned)
- Mean loudness deviation (aligned)
- Tempo stability metrics
- Dynamic range comparisons

It outputs visual charts and structured “insight cards” with actionable feedback.

---

## Core Features

### 🎼 Single Recording Analysis

- Tempo curve extraction
- Loudness curve extraction
- Automatic tempo interpretation (half-time / double-time detection)
- Tempo stability measurement (coefficient of variation)
- Dynamic range calculation

### 🎼 Student vs Reference Comparison

- DTW alignment based on loudness progression
- Aligned tempo difference curve
- Aligned loudness difference curve
- Mean |Δ BPM| metric
- Mean |Δ dB| metric
- Structured insight generation

### 📊 Visualization

- Interactive tempo difference chart
- Interactive loudness difference chart
- Clean frontend dashboard (React + Recharts)

---

## Insight Engine

The system generates human-readable performance feedback including:

- Overall tempo difference vs reference
- Tempo stability evaluation
- Tempo tracking consistency
- Loudness level comparison
- Dynamic range comparison
- Dynamics tracking consistency

Each insight includes:

- Severity classification (good / moderate / needs attention)
- Explanation
- Suggested next practice action

---

## Demo

1. Start the backend (FastAPI)
2. Start the frontend (Vite)
3. Open the web app and use **Compare (2 files)** to upload:
   - a student recording
   - a professional/reference recording
4. Review:
   - overlap + summary metrics
   - tempo and loudness difference charts
   - auto-generated insight cards

> Tip: Choose recordings of the same piece and similar sections for the most meaningful alignment.

---

## Setup

### Prerequisites

- **Python 3.10+** (recommended)
- **Node.js 18+**
- (Optional but helpful) FFmpeg installed and available in PATH if you plan to use formats beyond WAV.

---

### Backend (FastAPI)

```bash
cd backend

# Create + activate a virtual environment
python -m venv .venv

# Windows (Git Bash)
source .venv/Scripts/activate

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

# Run the API
python -m uvicorn main:app --reload
Backend will run at:

http://127.0.0.1:8000

Frontend (Vite + React)
cd frontend
npm install
npm run dev
Frontend will run at:

http://localhost:5173

Environment Variables (Optional)
If your backend runs somewhere else, set:

# frontend/.env
VITE_API_BASE=http://127.0.0.1:8000
Tech Stack
Backend
Python

FastAPI

Librosa (audio signal processing)

NumPy

Dynamic Time Warping (librosa.sequence.dtw)

Frontend
React (Vite)

Recharts (data visualization)

Fetch API

Core Concepts
Signal processing

Beat tracking

Time-series smoothing

Dynamic time warping

Feature normalization

Statistical analysis

Example Metrics
For a Chopin performance comparison:

Student recommended tempo: 57.7 BPM

Reference recommended tempo: 67.7 BPM

Mean aligned tempo deviation: ~11.7 BPM

Mean aligned loudness deviation: ~2.3 dB

The system automatically classifies these differences and generates practice guidance.

Why This Project
This project combines:

Software engineering

Audio signal processing

Data visualization

Classical music performance

It demonstrates the ability to:

Build full-stack applications

Design analytical pipelines

Align time-series data across variable-length inputs

Translate quantitative analysis into user-facing insights

Roadmap
Note-level alignment (pitch-based DTW)

Section-based segmentation

Multi-movement support

Improved perceptual loudness modeling (LUFS)

Performance history tracking

Status
Active development.
Currently supports solo piano recordings.

License
MIT

Motivation
This project combines my interest in classical music with software engineering to build a practical tool that helps musicians practice more effectively while demonstrating real-world data processing and visualization skills.
