import json


with open("shift.json", "r", encoding="utf-8") as f:
    shift_data = json.load(f)

summary = {}

for day in sorted(shift_data.keys(), key=int):
    for person in shift_data[day]:
        name = person["name"]
        hours = person.get("work_hours", 0)

        if name not in summary:
            summary[name] = {
                "総労働時間": 0,
                "work_days": [],
            }

        summary[name]["総労働時間"] += hours
        summary[name]["work_days"].append(int(day))

for name, data in summary.items():
    days = sorted(data["work_days"])
    max_streak = 0
    current_streak = 1 if days else 0

    for i in range(1, len(days)):
        if days[i] == days[i - 1] + 1:
            current_streak += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1

    max_streak = max(max_streak, current_streak)
    summary[name]["勤務日数"] = len(days)
    summary[name]["最大連続勤務日数"] = max_streak
    del summary[name]["work_days"]  # 一時リストは削除

print("\n📋 各スタッフの勤務集計\n")

for name, data in sorted(summary.items()):
    print(f"▼ {name}")
    print(f"  総労働時間：{data['総労働時間']}時間")
    print(f"  勤務日数　：{data['勤務日数']}日")
    print(f"  最大連続勤務日数：{data['最大連続勤務日数']}日\n")

with open("summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("✅ summary.json を出力しました。")
