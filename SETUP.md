

# Setup & Usage Guide

This document explains how to install dependencies, generate sample telemetry, run the backend API, and launch the web interface.

---

## Requirements

- Python 3.9+
- pip
- Git

Optional but recommended:
- Virtual environment (`venv`)

---

## 1) Clone the Repository

```bash
git clone <your-repo-url>
cd laptimeDecomp
```

---

## 2) Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

---

## 3) Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

If `requirements.txt` does not exist, install manually:

```bash
pip install flask pandas numpy
```

---

## 4) Generate Sample Telemetry

From project root:

```bash
python3 generate_telemetry.py --out data/big_telemetry.csv
```

This creates a large, realistic telemetry file for testing.

---

## 5) Run Backend API

From `backend/` directory:

```bash
python3 app.py
```

You should see:

```
Running on http://127.0.0.1:5001
```

Leave this terminal running.

---

## 6) Run Frontend

Open a second terminal:

```bash
cd frontend
python3 -m http.server 8000
```

Open browser:

```
http://localhost:8000
```

---

## 7) Use the App

1. Upload `data/big_telemetry.csv`
2. Choose number of segments (e.g., 8 or 12)
3. Brake threshold: `0.15`
4. Throttle threshold: `0.25`
5. Click **Analyze**

Results will appear in a ranked table.

---

## Common Issues

### Backend port already in use

Edit `backend/app.py`:

```python
app.run(debug=True, port=5002)
```

Then update the fetch URL in `frontend/script.js` accordingly.

---

### Python command not found

Try:

```bash
python3 --version
```

Use `python3` instead of `python`.

---

### CORS or fetch error

Make sure:

- Backend is running
- Frontend URL matches backend port

---

## Recommended Workflow

1. Generate telemetry
2. Start backend
3. Start frontend
4. Upload CSV
5. Inspect bottlenecks

---

## Next Steps

- Add real racing telemetry
- Tune thresholds
- Extend analyzer with more metrics

---

Happy hacking 🏁