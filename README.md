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

## Tech Stack

**Backend**
- Python
- FastAPI
- Librosa (audio signal processing)
- NumPy
- Dynamic Time Warping (librosa.sequence.dtw)

**Frontend**
- React (Vite)
- Recharts (data visualization)
- Fetch API

**Core Concepts**
- Signal processing
- Beat tracking
- Time-series smoothing
- Dynamic time warping
- Feature normalization
- Statistical analysis

---

## Example Metrics

For a Chopin performance comparison:

- Student recommended tempo: 57.7 BPM  
- Reference recommended tempo: 67.7 BPM  
- Mean aligned tempo deviation: ~11.7 BPM  
- Mean aligned loudness deviation: ~2.3 dB  

The system automatically classifies these differences and generates practice guidance.

---

## Why This Project

This project combines:

- Software engineering
- Audio signal processing
- Data visualization
- Classical music performance

It demonstrates the ability to:

- Build full-stack applications
- Design analytical pipelines
- Align time-series data across variable-length inputs
- Translate quantitative analysis into user-facing insights

---

## Roadmap

- Note-level alignment (pitch-based DTW)
- Section-based segmentation
- Multi-movement support
- Improved perceptual loudness modeling (LUFS)
- Performance history tracking

---

## Status

Active development.
Currently supports solo piano recordings.

---

## License

MIT


## Motivation
This project combines my interest in classical music with software engineering to build a practical tool that helps musicians practice more effectively while demonstrating real-world data processing and visualization skills.
