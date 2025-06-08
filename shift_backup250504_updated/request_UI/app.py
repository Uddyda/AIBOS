from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import matplotlib.pyplot as plt
from glob import glob
from io import BytesIO
import base64

app = Flask(__name__, template_folder='.')

# 定数設定
DATA_DIR = "data"
ADMIN_PASSWORD = "0000" #管理者パスワードの設定
os.makedirs(DATA_DIR, exist_ok=True)

working_hours = ["9-10", "10-11", "11-12", "12-13", "13-14", "14-15",
                 "15-16", "16-17", "17-18", "18-19", "19-20", "20-21"]

# グラフ生成（base64でHTMLに埋め込む）
def generate_schedule_base64_image():
    data_files = glob(os.path.join(DATA_DIR, "*.json"))
    if not data_files:
        return None

    staff_data = []
    for file in data_files:
        with open(file, "r", encoding="utf-8") as f:
            person = json.load(f)
            staff_data.append({"name": person["name"], "available": person["available"]})

    staff_data = sorted(staff_data, key=lambda x: x["name"])
    fig, ax = plt.subplots(figsize=(12, len(staff_data)))

    for i, person in enumerate(staff_data):
        for time in person["available"]:
            start_hour = int(time.split("-")[0])
            ax.barh(i, 1, left=start_hour, color='skyblue', edgecolor='black')
            ax.text(start_hour + 0.5, i, time, va='center', ha='center', fontsize=8)

    ax.set_yticks(range(len(staff_data)))
    ax.set_yticklabels([p["name"] for p in staff_data])
    ax.set_xticks(range(9, 22))
    ax.set_xticklabels([f"{h}:00" for h in range(9, 22)])
    ax.set_xlim(9, 21)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    return img_base64

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"].strip()
        return redirect(url_for("edit", name=name))

    img_base64 = generate_schedule_base64_image()
    return render_template("index.html", img_base64=img_base64)

@app.route("/edit/<name>", methods=["GET", "POST"])
def edit(name):
    path = os.path.join(DATA_DIR, f"{name}.json")

    if request.method == "POST":
        available = request.json.get("available", [])
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "available": available}, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "success"})

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            available = data.get("available", [])
    else:
        available = []

    return render_template("schedule.html", name=name, hours=working_hours, available=available)

@app.route("/lock", methods=["POST"])
def lock_submission():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "fail", "message": "パスワードが違います。"})

    request_data = []
    for path in glob(os.path.join(DATA_DIR, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            person = json.load(f)
            if "name" in person and "available" in person:
                request_data.append({
                    "name": person["name"],
                    "time": person["available"]  # ← キー名を "time" に変更
                })

    with open("../request.json", "w", encoding="utf-8") as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success", "message": "✅ request.json を作成しました。"})

if __name__ == "__main__":
    app.run(debug=True)
