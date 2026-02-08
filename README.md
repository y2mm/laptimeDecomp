# Lap Time Bottleneck Demo

This project is a **portfolio‑ready, end‑to‑end demo** that ingests
vehicle telemetry, breaks a lap into equal‑length segments, computes
per‑segment timing statistics and identifies where the driver is losing
the most time.  It ships with a simple Flask API and a lightweight
web frontend for interactive exploration.

## Features

- 📥 **CSV ingestion** – drop in a telemetry file with
  `timestamp`, `lap`, `speed`, `throttle`, `brake`, `steering` and
  `track_position` columns.
- 🧠 **Analysis pipeline** – sorts data per lap, computes time
  differences, segments laps and calculates average vs. best segment
  times.
- 📊 **Performance metrics** – reports average speed, throttle and
  brake usage per segment alongside timing loss and loss percentage.
- 🔎 **Ranking** – segments are ranked by time lost relative to the
  best performance so you immediately know where the biggest gains lie.
- 🌐 **API + UI** – includes a Flask endpoint for programmatic access
  and a clean HTML/JS frontend with a table and bar chart powered by
  Chart.js.

## Project Structure

```text
lap-time-bottleneck-demo/
├── backend/
│   ├── analyzer.py        # analysis functions (segmentation, timing, metrics)
│   ├── app.py            # Flask API exposing `/analyze` endpoint
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── index.html        # static webpage for uploading telemetry
│   └── script.js         # frontend logic (fetch + rendering)
├── data/
│   └── sample.csv        # generated sample telemetry for testing
└── README.md             # this documentation
```

## Getting Started

1. **Clone or download** this repository and navigate into the
   `lap-time-bottleneck-demo` directory.
2. **Install Python dependencies**:

   ```bash
   cd backend
   python -m venv venv
   . venv/bin/activate  # on Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Run the Flask API**:

   ```bash
   python app.py
   ```

   The API will start on `http://127.0.0.1:5000/analyze`.  It accepts
   `POST` requests with a `file` field containing a CSV and optional
   form fields `n_segments` (default `4`) and `max_dt` (to drop
   unrealistically large gaps in the data).

4. **Open the frontend**:

   For simplicity during local development you can open the HTML file
   directly in your browser:

   ```bash
   # From the root of this project
   open frontend/index.html  # macOS
   # or use xdg-open on Linux / WSL
   xdg-open frontend/index.html
   ```

   Alternatively, serve the frontend from a simple HTTP server to avoid
   any CORS issues:

   ```bash
   # In a separate terminal
   cd frontend
   python -m http.server 8000
   ```

   Then navigate to `http://localhost:8000` in your browser.  Upload
   `data/sample.csv` (or your own telemetry) and click **Analyze**.

## How It Works

1. **Segmenting the lap** – track positions are normalised from
   `0.0` (start/finish) to `1.0` and divided into `n` equal segments.
2. **Timing differences** – data is sorted per lap, then the
   difference between consecutive timestamps within each lap is
   computed.  Negative or zero deltas are discarded.  Optionally a
   `max_dt` threshold drops large gaps (e.g. telemetry dropouts).
3. **Aggregation** – total time spent in each segment is calculated
   per lap, then averaged across all laps.  The best (minimum) time
   per segment is found and subtracted from the average to produce
   `loss` and `loss_percent` metrics.
4. **Additional metrics** – average speed, throttle and brake usage are
   computed per segment to help explain why a bottleneck might exist.

The result is a table and bar chart ranking segments by time lost.
Segments with high loss values are your biggest improvement areas.

## Limitations & Future Work

- **Segment boundaries** are assigned on a per‑sample basis.  If a
  sample straddles two segments the entire time delta is credited to
  the next segment.  A more advanced approach would interpolate the
  segment boundary crossing to split the delta proportionally.
- **Corner detection** – the demo uses uniform segments rather than
  actual track corners.  Integrating track maps (GPS data) and
  curvature analysis could provide more meaningful “corners” for
  motorsport use.
- **Driver profiling** – cluster drivers by style (braking vs. throttle
  traces) or predict lap times with machine learning.  The current
  pipeline is designed to accommodate such extensions.

## License

This project is provided for demonstration purposes and does not
include any warranty.  Feel free to fork and modify for your own
portfolio or internal tools.

# Lap Time Bottleneck Finder

A **portfolio-ready motorsport telemetry analysis demo** that ingests raw vehicle telemetry, decomposes lap time into track segments, and automatically identifies where a driver is losing the most time (braking, corner exit, or late throttle).

This project demonstrates an end-to-end pipeline:
**Telemetry → Python Analysis → Flask API → Web UI**

---

## What It Does

- Upload a telemetry CSV file
- Split each lap into equal-length segments
- Compute average vs best time per segment
- Attribute time loss to:
  - Braking
  - Corner exit (powered exit)
  - Late throttle (delay after apex)
- Rank segments by largest performance opportunity

---

## Demo Screenshot

> *(Insert screenshot of the web UI here)*

Example:

```
[Screenshot showing upload box, results table, and ranked segments]
```

---

## Why This Project

This project showcases:

- Data engineering (cleaning, grouping, aggregation)
- Feature engineering from time-series telemetry
- Practical motorsport performance analytics
- Backend + API design with Flask
- Simple frontend visualization

It is designed to be easily extended into ML-based lap time prediction, driver profiling, or setup optimization.

---

## Project Structure

```text
laptimeDecomp/
├── backend/
│   ├── analyzer.py
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── script.js
├── data/
│   └── big_telemetry.csv
├── generate_telemetry.py
├── README.md
└── SETUP.md
```

---

## Interpreting the Loss Metrics

The reported loss values are **heuristic indicators**, not a full physical decomposition of lap time. They are designed to highlight *where to look first*, not to perfectly partition total lap time.

- **Brake Loss** – Extra time spent with the brake applied compared to your best lap in that segment. High values typically indicate braking earlier, longer, or more aggressively than necessary.

- **Exit Loss** – Extra time spent in the powered-exit phase (after throttle is re-applied) compared to your best lap. High values often point to poor exit speed, traction limitations, or weak acceleration.

- **Late Throttle Loss** – Extra time between the segment’s minimum speed (apex proxy) and when throttle is re-applied. High values suggest hesitation or delayed throttle pickup after the corner.

Because these metrics overlap in time and represent different behavioral signals, they **do not sum to the total Loss**. The *Top Cause* simply reflects which signal deviates the most from your best lap in that segment.

---

## Getting Started

Setup and run instructions are located in:

➡️ **[SETUP.md](SETUP.md)**

---

## Future Extensions

- Driver style clustering
- ML lap-time predictor
- Corner-based segmentation using GPS curvature
- Setup sensitivity analysis
- Strategy simulation

---

## License

Provided for demonstration and portfolio use.
# Lap Time Bottleneck Finder

A **portfolio-ready motorsport telemetry analysis demo** that ingests raw vehicle telemetry, decomposes lap time into track segments, and automatically identifies where a driver is losing the most time (braking, corner exit, or late throttle).

The project demonstrates an end-to-end pipeline:

**Telemetry → Python Analysis → Flask API → Web UI**

---

## Overview

Lap Time Bottleneck Finder helps answer a simple question:

> *Where am I actually losing lap time?*

By comparing your average performance to your best lap on a per-segment basis, the tool highlights the biggest opportunities for improvement and labels the dominant cause of time loss in each segment.

---

## Example Output

![alt text](Lap-Time-Bottleneck-Finder.png)

```
[Screenshot showing upload area, results table, and top causes per segment]
```

---

## Highlights

- Upload telemetry CSV
- Automatic lap segmentation
- Average vs best segment comparison
- Time-loss attribution (braking, corner exit, late throttle)
- Ranked performance bottlenecks

---

## Setup & Usage

Instructions for installing dependencies and running the project are located in:

➡️ **[SETUP.md](SETUP.md)**

---

## License

Provided for demonstration and portfolio use.