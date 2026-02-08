# 🎹 Classical Performance Diagnostic Tool

## Overview
Classical music students often reach a point where they can play all the notes of a piece, yet their performance still doesn’t sound stable or professional. The issue is usually not accuracy, but **tempo control and expressive timing** — problems that are difficult to diagnose by ear alone.

This project is a web-based tool that helps classical music students **quantitatively understand where and how their tempo and dynamics deviate** from a professional reference recording. By visualizing these differences over time and synchronizing them with audio playback, the tool turns subjective musical feedback into actionable, data-driven insight.

---

## Problem Statement
Musical interpretation in classical performance relies heavily on controlled tempo variation (rubato) and dynamics. Students often struggle to identify:
- where their tempo becomes unstable,
- why certain passages feel rushed or dragged,
- and how their interpretation differs from professional performances.

Traditional feedback methods rely on subjective listening or instructor input, which can be imprecise or unavailable during individual practice.

---

## Solution
This project analyzes audio recordings of classical performances to extract:
- **tempo over time**
- **dynamic (loudness) variation over time**

It then aligns and visualizes these features so students can:
- see where tempo variance increases,
- identify expressive moments and instabilities,
- compare their performance to a professional reference recording.

The result is a diagnostic tool that supports deliberate practice by showing *where* problems occur, not just that they exist.

---

## Core Features (v1)
- Upload a single classical music recording (solo instrument, piano-focused)
- Automatic extraction of:
  - tempo curve (BPM vs time)
  - loudness curve (perceptual proxy)
- Interactive visualization with synchronized audio playback
- Automatic detection of:
  - tempo instability
  - dynamic peaks and valleys
- Generated summary statistics:
  - average tempo
  - tempo variance
  - dynamic range

---

## Planned Enhancements (v1.5)
- Comparison mode between:
  - student performance
  - professional reference recording
- Overlayed tempo and dynamic curves
- Highlighted regions where the student significantly diverges from the reference
- Auto-generated “practice notes” identifying problematic passages

---

## Technical Focus
While rooted in music, this project is fundamentally an engineering exercise in:
- signal processing pipelines
- time-series analysis
- data normalization
- event detection
- frontend data visualization
- synchronizing real-time media playback with analytical data

The goal is correctness, interpretability, and reliability — not subjective musical judgment.

---

## Motivation
This project combines my interest in classical music with software engineering to build a practical tool that helps musicians practice more effectively while demonstrating real-world data processing and visualization skills.
