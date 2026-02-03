# AI Math Tutor (University AI Lab)

An interactive **AI-powered math tutor** built for a university Artificial Intelligence course lab.
It combines a sleek browser UI ("Galactic Math Challenge" theme) with a Flask backend that **adapts question difficulty** based on recent performance and response speed.

## What it does

- Generates arithmetic questions across **addition, subtraction, multiplication, division**
- Supports **Fixed difficulty** (Easy → Extreme) and an **Adaptive** mode
- Tracks per-skill performance (correct/total/mistakes), recent streaks, and response times
- Provides **instant coaching hints** after wrong answers
- Shows session analytics (accuracy, average time) + a simple “heatmap” of mistakes

## Why this is “AI” (in plain terms)

The tutor applies a lightweight adaptive policy:

- It watches your last few answers (a short performance window)
- It adjusts difficulty up when accuracy is high *and* you’re fast
- It adjusts difficulty down when you struggle (mistake streaks, low accuracy, very slow answers)
- It biases question selection toward the **weakest skill** (lowest accuracy) so practice is targeted

It’s intentionally simple and explainable—perfect for an AI lab where you want clear behavior, measurable signals, and easy iteration.

## Tech stack

- **Backend:** Python + Flask (REST endpoints)
- **Frontend:** Single-page HTML/CSS/JS
- **Storage:** Browser `localStorage` for “lifetime ops” stats

## Quickstart (macOS / Linux)

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python back.py
```

Then open your browser at:

- `http://127.0.0.1:5000`

## Quickstart (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py back.py
```

## How to play

1. Enter a player name
2. Choose a level (or **Adaptive**)
3. Start the mission
4. Answer questions; if you miss one, you’ll get a tip and the tutor will react

## API endpoints

The frontend calls these endpoints (base URL: `http://127.0.0.1:5000`):

- `POST /start` – start a session (name, duration, level)
- `GET /question` – get a new question
- `POST /answer` – submit an answer; returns correctness + hint + UI delay
- `GET /result` – get session stats and summary message

## Project structure

- `back.py` – Flask server + adaptive difficulty + session state
- `index.html` – UI (game flow, charts/heatmap canvas, audio)
- `Assets/` – sound effects and background music

## Notes / limitations

- Session state is in-memory (single-process). Refreshing/restarting the backend resets the session.
- CORS is permissive (`*`) for local development.
- This is designed as a course lab project—clean and demo-friendly over production-hardening.

## University context

Created for a **University AI course lab** project: **AI Math Tutor**.
If you’re reviewing this for grading, the key AI component is the explainable adaptive policy (performance window + response-time gating + weakest-skill targeting).

---

If you want, I can also add:
- screenshots / GIF section
- a short “grading rubric alignment” section
- a small architecture diagram
