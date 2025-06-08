import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json

# --- 火葬場枠と時間帯マッピング ---
cremation_time_map = {
    "1-a": "9-10", "1-b": "10-11", "1-c": "11-12", "1-d": "12-13",
    "1-e": "14-15", "1-f": "15-16", "1-g": "16-17", "1-h": "17-18",
    "2-a": "10-11", "2-b": "11-12", "2-c": "12-13", "2-d": "13-14",
    "2-e": "15-16", "2-f": "16-17", "2-g": "17-18", "2-h": "18-19",
    "3-a": "11-12", "3-b": "12-13", "3-c": "13-14", "3-d": "14-15",
    "3-e": "16-17", "3-f": "17-18", "3-g": "18-19", "3-h": "19-20",
    "4-a": "12-13", "4-b": "13-14", "4-c": "14-15", "4-d": "15-16",
    "4-e": "17-18", "4-f": "18-19", "4-g": "19-20", "4-h": "20-21"
}
working_hours = ["9-10", "10-11", "11-12", "12-13", "13-14", "14-15",
                 "15-16", "16-17", "17-18", "18-19", "19-20", "20-21"]
names = ["A", "B", "C", "D", "E"]

# --- 移動回数カウント関数（連続時間かつ火葬場番号が変化したときのみ加算） ---
def count_switch(staff):
    total = 0
    for person in staff:
        # 9-10 ～ 20-21 各時間帯の火葬場番号（未割当は "0"）のリストを作成
        crem_seq = [
            person[time][0] if person[time] not in (0, "x") else "0"
            for time in working_hours
        ]
        # 連続するペアを比較し、どちらも0以外かつ異なるときにカウント
        for i in range(len(crem_seq) - 1):
            curr = crem_seq[i]
            next_ = crem_seq[i + 1]
            if curr != "0" and next_ != "0" and curr != next_:
                total += 1
    return total



# --- 最小移動回数の割当て生成（ランダム試行ベース） ---
def generate_best_assignment(day_request, iterations=10000):
    best_staff = None
    best_score = float('inf')
    fallback_staff = None
    fallback_score = float('inf')
    total_slots = len(cremation_time_map)

    for _ in range(iterations):
        # staff 初期化（毎回 availability に基づいて生成）
        staff = []
        for entry in day_request:
            person = {"name": entry["name"]}
            for t in working_hours:
                person[t] = 0 if t in entry["time"] else "x"
            staff.append(person)

        crem_slots = list(cremation_time_map.items())
        random.shuffle(crem_slots)
        assigned_cremations = set()

        for crem_slot, time in crem_slots:
            assigned = False
            random.shuffle(staff)
            for person in staff:
                if person[time] == 0:  # 割当可能時間のみ
                    person[time] = crem_slot
                    assigned_cremations.add(crem_slot)
                    assigned = True
                    break

        score = count_switch(staff)
        assigned_count = len(assigned_cremations)

        if assigned_count == total_slots and score < best_score:
            best_score = score
            best_staff = [dict(p) for p in staff]

        if assigned_count > 0 and score < fallback_score:
            fallback_score = score
            fallback_staff = [dict(p) for p in staff]

    final_staff = best_staff if best_staff is not None else fallback_staff
    final_score = best_score if best_staff is not None else fallback_score

    if final_staff is not None:
        assigned_slots = sum(
            1 for person in final_staff for t in working_hours if person[t] not in (0, "x")
        )
        final_staff = sorted(final_staff, key=lambda x: x["name"])
    else:
        assigned_slots = 0

    return final_staff, final_score, assigned_slots
    


# --- グラフ描画用 ---
def plot_schedule(day, staff, score):
    slot_colors = {
        "a": "tab:orange", "b": "tab:red", "c": "tab:blue", "d": "tab:green",
        "e": "tab:orange", "f": "tab:red", "g": "tab:blue", "h": "tab:green"
    }
    crematoria = {"1": {}, "2": {}, "3": {}, "4": {}}
    print(staff)
    for person in staff:
        for time, slot in person.items():
            if time == "name" or slot == 0 or slot == "x":
                continue
            crem_id = slot.split("-")[0]
            crematoria[crem_id][time] = (person["name"], slot)

    fig, ax = plt.subplots(figsize=(12, 6))
    y_labels = ["line4", "line3", "line2", "line1"]
    for i, crem_id in enumerate(["4", "3", "2", "1"]):
        for time, (person, slot_label) in crematoria[crem_id].items():
            start_hour = int(time.split("-")[0])
            duration = 1
            slot_type = slot_label.split("-")[1]
            color = slot_colors.get(slot_type, "tab:gray")
            ax.barh(i, duration, left=start_hour, color=color, edgecolor='black')
            ax.text(start_hour + 0.5, i, f"{person}\n({slot_label})", va='center', ha='center', color='white', fontsize=8)

    ax.set_yticks(range(4))
    ax.set_yticklabels(y_labels)
    ax.set_xticks(range(9, 22))
    ax.set_xticklabels([f"{h}:00" for h in range(9, 22)])
    ax.set_xlim(9, 21)
    ax.set_title(f"day:{day} time schedule (count of switch: {score})")
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()

    # PNG画像として保存
    plt.savefig("shift_plot.png")

    plt.show()




#各従業員の労働時間の計算
def attach_labor_hours(staff):
    for person in staff:
        work_hours = sum(
            1 for t in working_hours if person[t] not in (0, "x")
        )
        person["work_hours"] = work_hours



# --- 実行部 ---
if __name__ == "__main__":

    shift_data = {}
    warnings = []
    weekly_work_hours = {}  # name → 総労働時間

    #シフト希望のファイルrequest.jsonを読み取り
    with open("request.json", "r", encoding="utf-8") as f:
        request_data = json.load(f)

    #各日付に対してシフトを作成＆画像出力
    for day in request_data:
        print(f"\n====== {day}日目のシフトを作成中 ======")

        day_request = request_data[day]

        staff, score, assigned_count = generate_best_assignment(day_request)
        total_slots = len(cremation_time_map)
        plot_schedule(day, staff, score)

        #総労働時間の追加
        attach_labor_hours(staff)
        for person in staff:
            name = person["name"]
            hours = person["work_hours"]
            weekly_work_hours[name] = weekly_work_hours.get(name, 0) + hours

        #staffごとの辞書を表示
        for person in staff:
            print(f"\n従業員 {person['name']} のシフト:　　　総労働時間:{person['work_hours']}時間")
            for t in working_hours:
                print(f"  {t}: {person[t]}")

        # shift.json に保存する構造に変換
        day_shift = []
        for person in staff:
            shift_dict = {k: v for k, v in person.items() if k in working_hours}
            day_shift.append({
                "name": person["name"],
                "work_hours": person["work_hours"],
                "shift": shift_dict
            })
        shift_data[day] = day_shift

        #不足時の警告
        if assigned_count < total_slots:
            warnings.append(f"{day}日目：{total_slots}枠のうち {assigned_count}枠しか埋められませんでした")
        else:
            print("✅ 正しくシフトが組めました")
    
    with open("shift.json", "w", encoding="utf-8") as f:
        json.dump(shift_data, f, ensure_ascii=False, indent=2)

    print("\n✅ shift.json に全日程のシフトを保存しました。")


    #組んだシフト内での各スタッフの総労働時間を出力
    print("\n🗓 各スタッフの1週間総労働時間：")
    for name in sorted(weekly_work_hours.keys()):
        print(f"  {name}: {weekly_work_hours[name]}時間")

    # 最後にまとめて警告を出力
    if warnings:
        print("\n⚠ 以下の日付でシフト人数が不足していました：")
        for line in warnings:
            print("  -", line)
    else:
        print("\n✅ 全日程、シフトはすべて埋まりました！")

