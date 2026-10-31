from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "study_care.db")

# ---------------------------------------------------------
# AI model
# This prototype trains a regression model on generated demo data.
# Replace this training data with ethically collected, consented
# real-world data before making scientific performance claims.
# ---------------------------------------------------------
def build_ai_model():
    rng = np.random.default_rng(42)
    n = 3000

    study_minutes = rng.integers(15, 91, n)
    accuracy = rng.uniform(35, 100, n)
    sleep_hours = rng.uniform(3, 10, n)
    posture_score = rng.integers(1, 6, n)  # 1=poor, 5=good
    fatigue = rng.integers(1, 6, n)        # 1=low, 5=high

    # Simulated learning-efficiency target for demonstration.
    ideal_duration = np.clip(
        48 + (sleep_hours - 7) * 5 + (accuracy - 70) * 0.12
        + (posture_score - 3) * 2 - (fatigue - 2) * 4,
        20, 75
    )
    duration_penalty = np.abs(study_minutes - ideal_duration) * 0.55
    score = (
        50 + (accuracy - 50) * 0.25
        + (sleep_hours - 6) * 4
        + (posture_score - 3) * 3
        - (fatigue - 2) * 5
        - duration_penalty
        + rng.normal(0, 4, n)
    )
    score = np.clip(score, 0, 100)

    X = np.column_stack([
        study_minutes, accuracy, sleep_hours, posture_score, fatigue
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, score, test_size=0.2, random_state=42
    )
    model = RandomForestRegressor(
        n_estimators=120, max_depth=12, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    return model, mae

AI_MODEL, MODEL_MAE = build_ai_model()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                study_minutes INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                sleep_hours REAL NOT NULL,
                posture_score INTEGER NOT NULL,
                fatigue INTEGER NOT NULL,
                focus INTEGER NOT NULL,
                predicted_score REAL NOT NULL,
                recommended_minutes INTEGER NOT NULL,
                actual_minutes INTEGER NOT NULL DEFAULT 0,
                notes TEXT DEFAULT ''
            )
        """)
        conn.commit()


def get_recommendation(data):
    sleep = float(data["sleep_hours"])
    accuracy = float(data["accuracy"])
    study = int(data["study_minutes"])
    posture = int(data["posture_score"])
    fatigue = int(data["fatigue"])
    focus = int(data.get("focus", 3))

    # Evaluate several possible study-block lengths with the trained model.
    candidates = np.array([25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    rows = np.column_stack([
        candidates,
        np.full(len(candidates), accuracy),
        np.full(len(candidates), sleep),
        np.full(len(candidates), posture),
        np.full(len(candidates), fatigue)
    ])
    predictions = AI_MODEL.predict(rows)
    best_index = int(np.argmax(predictions))
    recommended = int(candidates[best_index])
    predicted_score = float(predictions[best_index])

    # Practical feedback based on the supplied measurements.
    messages = []
    if sleep < 6:
        messages.append("수면 시간이 짧은 편이야. 오늘은 무리한 학습량보다 충분한 휴식을 우선해.")
    elif sleep < 7:
        messages.append("수면 시간이 다소 부족할 수 있어. 취침 시간을 조금 앞당겨 봐.")
    else:
        messages.append("입력한 수면 시간은 비교적 안정적인 편이야.")

    if fatigue >= 4:
        messages.append("피로도가 높게 입력됐어. 짧게 쉬고 몸 상태를 다시 확인해.")
    if posture <= 2:
        messages.append("자세 상태를 개선해 봐. 발을 바닥에 두고 화면 높이를 눈높이에 맞춰.")
    if focus <= 2:
        messages.append("집중도가 낮다고 느끼고 있어. 방해 요소를 줄이고 짧은 학습 블록부터 시작해.")
    if accuracy < 60:
        messages.append("정답률이 낮은 과목은 오답 원인을 분류하고 쉬운 문제부터 복습해.")
    elif accuracy >= 85:
        messages.append("정답률이 높은 편이야. 틀린 문제를 점검하며 학습을 유지해.")

    break_minutes = 10 if recommended >= 50 else 5
    return {
        "recommended_minutes": recommended,
        "break_minutes": break_minutes,
        "predicted_score": round(predicted_score, 1),
        "messages": messages,
        "model_mae": round(float(MODEL_MAE), 2),
        "model_note": "시뮬레이션 데이터로 학습한 시연용 모델이며 실제 학업 성과를 보장하지 않아."
    }


@app.route("/")
def index():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        history = conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT 8"
        ).fetchall()
        totals = conn.execute("""
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(actual_minutes), 0) AS total_minutes,
                   COALESCE(AVG(accuracy), 0) AS avg_accuracy
            FROM sessions
        """).fetchone()
    return render_template(
        "index.html",
        history=history,
        totals=totals,
        model_mae=round(float(MODEL_MAE), 2)
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    required = ["study_minutes", "accuracy", "sleep_hours",
                "posture_score", "fatigue", "focus"]
    try:
        for key in required:
            if key not in data:
                return jsonify({"error": f"필수 항목이 없어: {key}"}), 400

        values = {
            "study_minutes": int(data["study_minutes"]),
            "accuracy": float(data["accuracy"]),
            "sleep_hours": float(data["sleep_hours"]),
            "posture_score": int(data["posture_score"]),
            "fatigue": int(data["fatigue"]),
            "focus": int(data["focus"])
        }
        if not (0 <= values["study_minutes"] <= 1440):
            raise ValueError("공부 시간은 0~1440분으로 입력해 줘.")
        if not (0 <= values["accuracy"] <= 100):
            raise ValueError("정답률은 0~100%로 입력해 줘.")
        if not (0 <= values["sleep_hours"] <= 24):
            raise ValueError("수면 시간은 0~24시간으로 입력해 줘.")
        for key in ["posture_score", "fatigue", "focus"]:
            if not 1 <= values[key] <= 5:
                raise ValueError("자세·피로도·집중도는 1~5로 입력해 줘.")

        result = get_recommendation(values)
        result["input"] = values
        return jsonify(result)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/session", methods=["POST"])
def save_session():
    data = request.get_json(silent=True) or {}
    try:
        required = ["study_minutes", "accuracy", "sleep_hours",
                    "posture_score", "fatigue", "focus",
                    "predicted_score", "recommended_minutes", "actual_minutes"]
        if any(k not in data for k in required):
            return jsonify({"error": "저장에 필요한 데이터가 부족해."}), 400

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO sessions (
                    created_at, study_minutes, accuracy, sleep_hours,
                    posture_score, fatigue, focus, predicted_score,
                    recommended_minutes, actual_minutes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                int(data["study_minutes"]), float(data["accuracy"]),
                float(data["sleep_hours"]), int(data["posture_score"]),
                int(data["fatigue"]), int(data["focus"]),
                float(data["predicted_score"]),
                int(data["recommended_minutes"]),
                int(data["actual_minutes"]),
                str(data.get("notes", ""))[:300]
            ))
            conn.commit()
        return jsonify({"ok": True, "message": "학습 기록을 저장했어."})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/history")
def api_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT created_at, actual_minutes, accuracy, predicted_score
            FROM sessions ORDER BY id DESC LIMIT 20
        """).fetchall()
    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
