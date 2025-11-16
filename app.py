import os
import random
from flask import Flask, render_template, request, jsonify

# ---------------------------
# Optional: Generic HTTP LLM client
# ---------------------------
def call_llm_via_http(prompt: str, api_url: str, api_key: str = None, model: str = None, extra: dict = None, timeout: int = 30):
    """
    Call a simple HTTP LLM endpoint that accepts JSON like:
      { "prompt": "...", "model": "..." }
    and returns JSON with a text field: "output" | "text" | "response" | "completion" | "result".
    Returns None on any failure so the caller can fall back gracefully.
    """
    if not api_url:
        return None
    try:
        import requests
        payload = {"prompt": prompt}
        if model:
            payload["model"] = model
        if extra:
            payload.update(extra)
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        for key in ("output", "text", "response", "completion", "result"):
            if isinstance(data, dict) and key in data:
                val = data[key]
                if isinstance(val, dict):
                    for k2 in ("text", "content", "message", "output"):
                        if k2 in val:
                            return str(val[k2])
                    return str(val)
                return str(val)
        if isinstance(data, list) and data:
            return str(data[0])
        if isinstance(data, str):
            return data
        return str(data)
    except Exception:
        return None

# ---------------------------
# Storage (SQLite)
# ---------------------------
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("data", "app.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            weight REAL,
            height REAL,
            bmi REAL,
            question TEXT,
            reply TEXT,
            source TEXT
        )
        """)
        conn.commit()

def save_chat_row(name: str, age: int, weight: float, height: float, bmi: float, question: str, reply: str, source: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chats (created_at, name, age, weight, height, bmi, question, reply, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), name, age, weight, height, bmi, question, reply, source))
        conn.commit()


reminders = [
    "💧 Don’t forget to drink water!",
    "🚶 Time for a walk break.",
    "🧘 Do a quick 2 min stretch.",
    "🍎 Eat a fruit instead of junk food."
]

# Simulated step count
def get_step_count():
    return random.randint(2000, 12000)

# Calculate BMI
def calculate_bmi(weight, height):
    height_m = height / 100
    if height_m <= 0:
        return None
    return round(weight / (height_m ** 2), 2)

# Health status based on BMI
def bmi_status(bmi):
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight 😟"
    elif 18.5 <= bmi < 24.9:
        return "Normal ✅"
    elif 25 <= bmi < 29.9:
        return "Overweight ⚠️"
    else:
        return "Obese 🚨"

# ---------------------------
# Offline fallback assistant
# ---------------------------
def offline_coach_response(name: str, age: int, weight: int, height: int, bmi: float, question: str) -> str:
    """Simple heuristic response used when no LLM endpoint is available."""
    status = bmi_status(bmi)
    base_intro = f"Hi {name if name else 'there'}! Your BMI is {bmi} ({status}). "
    q = (question or "").lower()

    # Diet guidance
    if any(k in q for k in ["diet", "meal", "food", "eat", "nutrition", "calorie"]):
        if bmi is None:
            plan = (
                "- Breakfast: Oats 60g with milk/yogurt, 1 fruit, 10 nuts\n"
                "- Lunch: Mixed veg bowl (2 cups) + dal 1 cup + brown rice 1 cup or 2 chapati\n"
                "- Snack: Greek yogurt 150g or sprouts bowl 1 cup\n"
                "- Dinner: Grilled paneer/tofu/chicken 130–150g + salad 2 cups\n"
            )
            return base_intro + "Here’s a balanced one-day plan:\n" + plan + "Hydrate 2–3L/day."
        # Tailor portions and macros by BMI range
        if bmi < 18.5:
            plan = (
                "- Breakfast: Oats 80g with milk/yogurt, 1 banana, 15 nuts\n"
                "- Lunch: 2 cups veg + dal 1.5 cups + rice 1.5 cups or 3 chapati + 1 tsp ghee\n"
                "- Snack: Peanut butter sandwich (2 slices) or chana chaat 1.5 cups\n"
                "- Dinner: Paneer/tofu/chicken 170–200g + rice 1–1.5 cups + salad 1 cup\n"
                "- Add-ons: 1 cup milk or yogurt after dinner if needed\n"
            )
            return base_intro + "Goal: gentle surplus to gain lean mass.\n" + plan + "Protein 1.6–2.0g/kg, 7–8h sleep."
        if bmi < 25:
            plan = (
                "- Breakfast: Oats 60g with milk/yogurt, 1 fruit, 10 nuts\n"
                "- Lunch: 2 cups veg + dal 1 cup + rice 1 cup or 2 chapati\n"
                "- Snack: Greek yogurt 150g or sprouts 1 cup\n"
                "- Dinner: Paneer/tofu/chicken 140–170g + salad 2 cups + small carb (½ cup rice or 1 chapati)\n"
            )
            return base_intro + "Goal: maintenance with high protein and fiber.\n" + plan + "Hydrate 2–3L/day."
        if bmi < 30:
            plan = (
                "- Breakfast: Veg omelet (2 eggs) or tofu scramble + oats 40g\n"
                "- Lunch: 2 cups veg + dal/beans 1–1.2 cups + brown rice ½–1 cup or 1–2 chapati\n"
                "- Snack: Fruit + 10 nuts or buttermilk 250ml\n"
                "- Dinner: Paneer/tofu/chicken 150–180g + salad 2–3 cups (olive oil 1 tsp)\n"
            )
            return base_intro + "Goal: mild calorie deficit with adequate protein.\n" + plan + "Aim 7–9k steps/day."
        else:
            plan = (
                "- Breakfast: Greek yogurt 200g + berries/fruit + chia 1 tbsp\n"
                "- Lunch: Large salad (3 cups) + paneer/tofu/chicken 170–200g + dal ¾ cup\n"
                "- Snack: Sprouts 1 cup or whey/soy shake\n"
                "- Dinner: Non-starchy veg 3 cups + lean protein 170–200g\n"
            )
            return base_intro + "Goal: higher protein, higher fiber, lower refined carbs.\n" + plan + "Hydrate 2.5–3L/day."

    # Workout guidance
    if any(k in q for k in ["workout", "exercise", "gym", "training", "run", "walk"]):
        return (
            base_intro
            + "Try a simple 20–25 min routine:\n"
            + "1) Warm-up 3 min (march in place, arm circles)\n"
            + "2) 3 rounds: 40s bodyweight squats, 40s push-ups (knee ok), 40s glute bridge, 40s plank, 40s rest\n"
            + "3) Finish with 5–8 min easy walk and stretches.\n"
            + "Aim 7–9k steps/day on non-gym days."
        )

    # Weight management
    if any(k in q for k in ["weight", "fat", "lose", "gain", "bulk", "cut"]):
        tip = "For fat loss, keep a mild calorie deficit and 1.6–2.2g protein/kg body weight."
        if bmi and bmi < 18.5:
            tip = "Focus on a slight calorie surplus with 1.6–2.0g protein/kg and progressive strength training."
        return base_intro + tip + " Track steps and sleep 7–8 hours."

    # General health
    return (
        base_intro
        + "General tips: 7–8h sleep, 7–9k steps/day, 2–3L water, protein each meal, and strength training 2–3x/week."
    )

app = Flask(__name__, static_folder="static", template_folder="templates")
init_db()

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/chat")
def chat():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or os.getenv("USER") or "User").strip()
    try:
        age = int(data.get("age") or 25)
    except Exception:
        age = 25
    try:
        weight = float(data.get("weight") or 70)
    except Exception:
        weight = 70
    try:
        height = float(data.get("height") or 170)
    except Exception:
        height = 170
    question = data.get("message") or ""
    bmi = calculate_bmi(weight, height)

    # Try LLM if configured via environment; otherwise fall back to offline coach
    llm_api_url = (os.getenv("LLM_API_URL") or "").strip()
    llm_api_key = (os.getenv("LLM_API_KEY") or "").strip()
    llm_model = (os.getenv("LLM_MODEL") or "gemini-flash-2.5-pro").strip()

    reply = None
    if llm_api_url:
        prompt = (
            f"You are a helpful, accurate assistant.\n"
            f"User name: {name if name else 'User'}\n"
            f"Age: {age}, Weight: {weight} kg, Height: {height} cm, BMI: {bmi}\n"
            f"Question: {question}\n"
            f"Give a concise, practical answer. If giving a meal plan, include portion sizes."
        )
        llm_reply = call_llm_via_http(prompt=prompt, api_url=llm_api_url, api_key=llm_api_key, model=llm_model)
        if llm_reply:
            reply = llm_reply
            source = "llm"
        else:
            reply = offline_coach_response(name, age, weight, height, bmi, question)
            source = "offline"
    if not reply:
        reply = offline_coach_response(name, age, weight, height, bmi, question)
        source = "offline"

    # Persist chat row; ignore errors to avoid user-visible failures
    try:
        save_chat_row(name, age, weight, height, bmi, question, reply, source)
    except Exception:
        pass

    return jsonify({
        "reply": reply,
        "bmi": bmi,
        "bmi_status": bmi_status(bmi),
        "steps_today": get_step_count(),
        "reminder": random.choice(reminders),
    })

@app.get("/history")
def history():
    limit = int(request.args.get("limit", 100))
    import sqlite3 as _sqlite
    with _sqlite.connect(DB_PATH) as conn:
        conn.row_factory = _sqlite.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM chats ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.get("/export.csv")
def export_csv():
    def generate():
        import sqlite3 as _sqlite
        with _sqlite.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, created_at, name, age, weight, height, bmi, question, reply, source FROM chats ORDER BY id DESC")
            yield "id,created_at,name,age,weight,height,bmi,question,reply,source\r\n"
            for row in cur.fetchall():
                def esc(v):
                    s = "" if v is None else str(v)
                    if any(c in s for c in [',', '"', '\n', '\r']):
                        s = '"' + s.replace('"', '""') + '"'
                    return s
                yield ",".join(esc(v) for v in row) + "\r\n"
    from flask import Response as _Response
    return _Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=chat_history.csv"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
