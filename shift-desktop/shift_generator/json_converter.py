import json
import os
import sys

"""
Usage:
  python json_converter.py <DEFINE_JSON_PATH> [NEW_JSON_PATH] [ROKUYOU_JSON_PATH]

Args:
  DEFINE_JSON_PATH : 旧JSON (define.json) のパス（必須）
  NEW_JSON_PATH    : 変換後 new.json の出力パス（省略時: CWD/new.json）
  ROKUYOU_JSON_PATH: 六曜JSON (rokuyou.json) のパス（省略時: スクリプト隣の rokuyou.json）
"""

def parse_args():
    if len(sys.argv) < 2:
        print("Usage: python json_converter.py <DEFINE_JSON_PATH> [NEW_JSON_PATH] [ROKUYOU_JSON_PATH]")
        sys.exit(1)
    define_path = sys.argv[1]
    new_json_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(os.getcwd(), "new.json")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rokuyou_default = os.path.join(script_dir, "rokuyou.json")
    rokuyou_path = sys.argv[3] if len(sys.argv) >= 4 else rokuyou_default
    return define_path, new_json_path, rokuyou_path

def create_calendar(year: int, rokuyou_path: str):
    with open(rokuyou_path, "r", encoding="utf-8") as f:
        rokuyou_data = json.load(f)

    found = None
    for entry in rokuyou_data:
        if entry.get("year") == year:
            found = entry
            break
    if not found:
        raise ValueError(f"rokuyou.json に year={year} のカレンダーが見つかりません: {rokuyou_path}")

    input_calendar = found["calendar"]
    month_names = [
        "April","May","June","July","August","September",
        "October","November","December","January","February","March"
    ]

    data = {}
    for m_name in month_names:
        if m_name not in input_calendar:
            continue
        days_list = input_calendar[m_name]
        days_in_month = max(item["day"] for item in days_list) if days_list else 0
        friend_days = [item["day"] for item in days_list if item.get("rokuyo") == "友引"]
        data[m_name] = {
            "days_in_month": days_in_month,
            "friend_days": friend_days
        }
    return data

def transform_data(old_json, rokuyou_path: str):
    new_json = {}

    optimize_headcount = old_json.get("optimize_headcount", False)
    new_json["optimize_headcount"] = optimize_headcount

    year = old_json.get("year", 2025)
    new_json["year"] = year


    months = old_json.get("months", [])
    new_json["months"] = months


    new_json["positions"] = {}
    expanded_roles = {}
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    roles_data = old_json.get("roles", {})
    for role_name, role_info in roles_data.items():
        rtype = role_info.get("type", "dummy")
        count = role_info.get("count", 1)
        names = []
        for i in range(count):
            suffix = alpha[i] if i < len(alpha) else f"X{i}"
            name = f"{role_name}{suffix}"
            new_json["positions"][name] = rtype
            names.append(name)
        expanded_roles[role_name] = names

    dummy_names = [f"N{i}" for i in range(1, 21)]
    new_json["priority_assignments"] = {}
    capability_data = old_json.get("role_capability", {})
    for work_key, cap in capability_data.items():
        p_roles = cap.get("primary", [])
        s_roles = cap.get("secondary", [])
        expanded_primary = [n for r in p_roles for n in expanded_roles.get(r, [])]
        expanded_secondary = [n for r in s_roles for n in expanded_roles.get(r, [])]
        new_json["priority_assignments"][work_key] = {
            "primary": expanded_primary,
            "secondary": expanded_secondary,
            "third": dummy_names,
        }

    if "daily_requirements" in old_json:
        new_json["daily_requirements"] = {}
        for key, val in old_json["daily_requirements"].items():
            new_json["daily_requirements"][key] = {
                "normal_min": val.get("normal_min", 0),
                "normal_max": val.get("normal_max", 0),
                "friend_min": val.get("friend_min", 0),
                "friend_max": val.get("friend_max", 0),
            }

    if "work_constraints" in old_json:
        wc_old = old_json["work_constraints"]
        new_json["work_constraints"] = {}
        for wtype in ["employee", "part_timer", "dummy"]:
            if wtype in wc_old:
                new_json["work_constraints"][wtype] = {
                    "days_off_per_7days": wc_old[wtype].get("weekly_days_off", 0),
                    "max_consecutive_days": wc_old[wtype].get("max_consecutive_days", 0),
                    "min_monthly_workdays": wc_old[wtype].get("min_monthly_workdays", 0),
                }

    for dn in [f"N{i}" for i in range(1, 21)]:
        new_json["positions"].setdefault(dn, "dummy")

    type_order = {"employee": 0, "part_timer": 1, "dummy": 2}
    new_json["positions"] = dict(sorted(new_json["positions"].items(), key=lambda x: type_order.get(x[1], 99)))

    new_json["calendar"] = create_calendar(year, rokuyou_path)
    return new_json

def main():
    define_path, new_json_path, rokuyou_path = parse_args()
    with open(define_path, "r", encoding="utf-8") as f:
        old_data = json.load(f)
    new_data = transform_data(old_data, rokuyou_path)
    os.makedirs(os.path.dirname(new_json_path), exist_ok=True)
    with open(new_json_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("✅ 変換が完了しました。")
    print(f"入力: {define_path}")
    print(f"六曜: {rokuyou_path}")
    print(f"出力: {new_json_path}")
    print(f"old_data: {len(old_data.get('months', []))} months, {len(old_data.get('roles', {}))} roles")

if __name__ == "__main__":
    main()
