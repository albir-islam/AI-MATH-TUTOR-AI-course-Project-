from flask import Flask, request, jsonify, render_template
import random
import time
from collections import Counter
from statistics import mean
import os

app = Flask(__name__, template_folder=".")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

SESSION = {
    "player": None,
    "level": "Easy",
    "start_time": None,
    "duration": 180,
    "skills": {
        "addition": {"correct": 0, "total": 0, "mistakes": 0},
        "subtraction": {"correct": 0, "total": 0, "mistakes": 0},
        "multiplication": {"correct": 0, "total": 0, "mistakes": 0},
        "division": {"correct": 0, "total": 0, "mistakes": 0}
    },
    "current": None,
    "asked_questions": set(),
    "history_log": [],
    "error_patterns": {"sub_borrowing": 0, "mul_table": 0, "div_inverse": 0},
    "response_times": [],
    "prev_wrong": False
}

LEVELS_ORDER = ["Easy", "Medium", "Hard", "Extreme"]

LEVEL_OPS = {
    "Easy": ["addition", "subtraction"],
    "Medium": ["addition", "subtraction", "multiplication"],
    "Hard": ["addition", "subtraction", "multiplication", "division"],
    "Extreme": ["addition", "subtraction", "multiplication", "division"] 
}

@app.route("/")
def home():
    return render_template("index.html")


def accuracy(skill):
    s = SESSION["skills"][skill]
    return s["correct"] / s["total"] if s["total"] else 0.0


def adaptive_difficulty():
    current_lvl = SESSION.get("level", "Easy")
    if current_lvl not in LEVELS_ORDER:
        current_lvl = "Easy"
        
    idx = LEVELS_ORDER.index(current_lvl)
    
    history = SESSION.get("history_log", [])
    recent = history[-5:]
    
    streak_mistakes = 0
    for res in reversed(history):
        if not res: streak_mistakes += 1
        else: break
            
    times = SESSION.get("response_times", [])
    recent_times = times[-5:]
    avg_time = mean(recent_times) if len(recent_times) > 0 else 10

    time_limit = {0: 10, 1: 7, 2: 5}
    
    if len(recent) >= 5:
        correct_count = sum(recent)

        if correct_count >= 4 and idx < 3:
            if avg_time < time_limit.get(idx, 5):
                return LEVELS_ORDER[idx + 1]

        elif idx > 0:
            if streak_mistakes >= 2:
                return LEVELS_ORDER[idx - 1]
            if correct_count <= 2:
                return LEVELS_ORDER[idx - 1]
            if avg_time > 15:
                return LEVELS_ORDER[idx - 1]
            
    return current_lvl


def get_hint(topic):
    level = SESSION.get("level", "Easy")

    if topic == "addition":
        return (
            "Addition tip: Make a 10/20/100 first, then add what's left. "
            "Example: 8+7 = 8+2+5. Add tens, then ones."
        )
    if topic == "subtraction":
        return (
            "Subtraction tip: Subtract in parts (big jump, then adjust). "
            "Example: 19−7 = (19−10)+3. You can also check by adding back."
        )
    if topic == "multiplication":
        return (
            "Multiplication tip: Break a factor and use the distributive rule. "
            "Example: 6×7 = 6×5 + 6×2."
        )
    if topic == "division":
        if level == "Extreme":
            return (
                "Division tip (Extreme): Use multiplication + remainder; decimals may appear. "
                "Example: 25÷4: 4×6=24, remainder 1 → 1/4=0.25 → 6.25."
            )
        return (
            "Division tip: Think inverse multiplication. "
            "Find the number c so divisor×c = dividend (e.g., 21÷7 → 7×?=21)."
        )
    return "Tip: Slow down, do one step at a time, then quickly sanity-check."


def generate_question():
    for _ in range(10):
        if SESSION.get("mode") == "Adaptive":
            level = adaptive_difficulty()
            SESSION["level"] = level
        else:
            level = SESSION["level"]
        allowed = LEVEL_OPS.get(level, ["addition", "subtraction"])

        allowed_sorted = sorted(allowed, key=lambda k: accuracy(k))

        if random.random() < 0.5:
            topic = allowed_sorted[0]
        else:
            topic = random.choice(allowed)

        if level == "Easy":
            add_range = (1, 20); sub_range = (1, 20); mul_range = (1, 5); div_range = (1, 10)
        elif level == "Medium":
            add_range = (10, 50); sub_range = (10, 50); mul_range = (2, 10); div_range = (2, 10)
        elif level == "Hard":
            add_range = (50, 100); sub_range = (20, 100); mul_range = (5, 15); div_range = (5, 15)
        else:
            add_range = (100, 500); sub_range = (100, 500); mul_range = (10, 20); div_range = (10, 20)

        q_str = ""; ans = 0

        if topic == "addition":
            a, b = random.randint(*add_range), random.randint(*add_range)
            ans = a + b; q_str = f"{a} + {b}"
        elif topic == "subtraction":
            a, b = random.randint(*sub_range), random.randint(*sub_range)
            if a < b: a, b = b, a
            ans = a - b; q_str = f"{a} - {b}"
        elif topic == "multiplication":
            a, b = random.randint(*mul_range), random.randint(*mul_range)
            ans = a * b; q_str = f"{a} × {b}"
        elif topic == "division":
            if level == "Extreme":
                divisor = random.randint(2, 10)
                dividend = random.randint(*div_range) * random.randint(1, 3) 
                if random.random() < 0.4: dividend += 1
                
                ans = round(dividend / divisor, 2)
                q_str = f"{dividend} ÷ {divisor}"
            else:
                res, divisor = random.randint(*div_range), random.randint(2, 10)
                dividend = res * divisor
                ans = res
                q_str = f"{dividend} ÷ {divisor}"

        if q_str not in SESSION["asked_questions"]:
            SESSION["asked_questions"].add(q_str)
            SESSION["current"] = {
                "topic": topic, "answer": ans, 
                "q_start": time.time()
            }
            help_text = ""
            if SESSION.get("prev_wrong", False):
                help_text = get_hint(topic)
                SESSION["prev_wrong"] = False
                
            return {"question": q_str, "level": level, "help": help_text}

    return {"question": q_str, "level": level, "help": ""}


@app.route("/start", methods=["POST"])
def start_game():
    data = request.get_json(silent=True) or {}
    SESSION["player"] = data.get("name", "Player")
    SESSION["duration"] = int(data.get("duration", 180))
    
    in_level = data.get("level", "Easy")
    if in_level == "Adaptive":
        SESSION["mode"] = "Adaptive"
        SESSION["level"] = "Easy"
    else:
        lvl_map = {"3": "Easy", "4": "Medium", "5": "Hard", "6": "Extreme"}
        SESSION["mode"] = "Fixed"
        if in_level in lvl_map: SESSION["level"] = lvl_map[in_level]
        else: SESSION["level"] = in_level if in_level in LEVELS_ORDER else "Easy"

    SESSION["start_time"] = time.time()
    SESSION["asked_questions"] = set()
    SESSION["history_log"] = []
    SESSION["error_patterns"] = {"sub_borrowing": 0, "mul_table": 0, "div_inverse": 0}
    SESSION["response_times"] = []
    SESSION["prev_wrong"] = False
    
    for k in SESSION["skills"]:
        SESSION["skills"][k] = {"correct": 0, "total": 0, "mistakes": 0}
    return jsonify({"status": "started"})


@app.route("/question")
def question():
    return jsonify(generate_question())


@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json(silent=True) or {}
    q = SESSION.get("current")
    if q is None:
        return jsonify({"error": "no_active_question"}), 400

    user_ans = data.get("answer")
    if user_ans is None or user_ans == "":
        return jsonify({"correct": False, "hint": "Please enter a number."})
    t_taken = time.time() - q.get("q_start", time.time())
    SESSION["response_times"].append(t_taken)

    try:
        user_val = float(user_ans)
        correct_val = float(q["answer"])
        correct = abs(user_val - correct_val) < 0.05
    except ValueError:
        correct = False
        user_val = 0

    skill = q["topic"]
    SESSION["skills"][skill]["total"] += 1
    SESSION["history_log"].append(correct)
    
    hint_msg = ""
    if correct:
        SESSION["skills"][skill]["correct"] += 1
        SESSION["prev_wrong"] = False
    else:
        SESSION["skills"][skill]["mistakes"] += 1
        hint_msg = get_hint(skill)
        SESSION["prev_wrong"] = True
        
        if skill == "subtraction" and abs(user_val - correct_val) % 10 == 0:
            SESSION["error_patterns"]["sub_borrowing"] += 1
        elif skill == "multiplication":
             SESSION["error_patterns"]["mul_table"] += 1
        elif skill == "division":
             SESSION["error_patterns"]["div_inverse"] += 1

    current_level = SESSION.get("level", "Easy")
    delays = {
        "Easy": 1500,
        "Medium": 1200,
        "Hard": 900,
        "Extreme": 600
    }
    
    delay_ms = delays.get(current_level, 1500)

    return jsonify({
        "correct": correct,
        "hint": hint_msg,
        "delay": delay_ms
    })


@app.route("/result")
def result():
    skills = SESSION["skills"]
    heatmap = {k: v["mistakes"] for k, v in skills.items()}
    
    mastery_report = []
    for s, data in skills.items():
        if data["total"] > 0:
            m_score = (data["correct"] - data["mistakes"] * 0.5) / data["total"]
            m_score = max(0, m_score) * 100
            mastery_report.append(f"{s.capitalize()}: {int(m_score)}%")

    times = SESSION.get("response_times", [])
    avg_time = mean(times) if times else 0
    speed_msg = ""
    if avg_time < 5: speed_msg = "You are a speed demon!"
    elif avg_time < 10: speed_msg = "Good maintainable pace."
    else: speed_msg = "You take your time to be precise."

    total_acc = sum(SESSION["history_log"])/len(SESSION["history_log"]) if SESSION["history_log"] else 0
    if total_acc > 0.8 and avg_time > 15:
        speed_msg = "You are slow but very accurate. Try to speed up!"
    elif total_acc < 0.5 and avg_time < 5:
        speed_msg = "You answer quickly but make mistakes. Slow down!"

    full_msg = f"{speed_msg}\n" + " | ".join(mastery_report)

    return jsonify({
        "player": SESSION["player"],
        "skills": SESSION["skills"],
        "heatmap": heatmap,
        "message": full_msg,
        "avg_time": round(avg_time, 2)
    })


if __name__ == "__main__":
    if os.environ.get("RUN_TESTS") == "1":
        pass
    else:
        print("Starting Flask server at http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
