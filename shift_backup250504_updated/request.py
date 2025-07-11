import json

# --- 従業員ごとの労働可能時間（必要に応じて変更） ---
request = [
    {"name": "A", "time": ["9-10", "10-11", "11-12", "12-13"]},
    {"name": "B", "time": ["10-11", "11-12", "12-13", "13-14", "14-15"]},
    {"name": "C", "time": ["11-12", "12-13", "13-14", "14-15", "15-16", "16-17"]},
    {"name": "D", "time": ["12-13", "13-14", "14-15", "15-16", "16-17", "17-18"]},
    {"name": "E", "time": ["14-15", "15-16", "16-17", "17-18", "18-19", "19-20", "20-21"]}
]

# --- JSON ファイルとして保存 ---
with open("request.json", "w", encoding="utf-8") as f:
    json.dump(request, f, ensure_ascii=False, indent=2)

print("✅ request.json を作成しました。")
