import json
import datetime
import calendar

# 追加: 六曜判定用ライブラリ
# pip install rokuyou
from rokuyou import Rokuyou

# 旧JSONファイルのパス
JSON_BEFORE = "./server/output/sample.json"
# 変換後の新JSONファイルのパス
JSON_AFTER = "./new.json"

def create_calendar(year: int):
    """
    指定した year について、1月～12月の各日付を取得。
    六曜ライブラリ(rokuyou)を使って友引の日のみを抽出して返す。
    
    戻り値サンプル:
    {
      "January": {
         "days_in_month": 31,
         "friend_days": [1, 6, 11, ...]
      },
      "February": {
         "days_in_month": 29,
         "friend_days": [...]
      },
      ...
      "December": { ... }
    }
    """
    # 月英名と対応させるためのリスト
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    data = {}

    for month in range(1, 13):
        # 該当月の日数を取得
        days_in_month = calendar.monthrange(year, month)[1]

        # 友引の日を探す
        friend_days = []
        for day in range(1, days_in_month + 1):
            dt = datetime.date(year, month, day)
            r = Rokuyou(dt)
            if r.rokuyou_jp == "友引":
                friend_days.append(day)

        data[month_names[month - 1]] = {
            "days_in_month": days_in_month,
            "friend_days": friend_days
        }

    return data


def transform_data(old_json):
    """
    旧JSON -> 新JSON への変換ロジック。
    1) roles を展開して positions を作成
    2) role_capability を使って priority_assignments を生成
       （各 priority に展開後の従業員名を割り当て、 third に dummyを20名）
    3) daily_requirements, work_constraints, year をそのまま or 必要に応じて変換コピー
    4) 最終的に positions を type順でソート
    5) (追加) 指定した year からカレンダーを作り "calendar" キーで格納
    """

    new_json = {}

    #
    # (1) year
    #
    year = old_json.get("year", 2025)
    new_json["year"] = year

    #
    # (2) roles => positions の展開
    #
    new_json["positions"] = {}
    expanded_roles = {}
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    roles_data = old_json.get("roles", {})
    for role_name, role_info in roles_data.items():
        rtype = role_info.get("type", "dummy")  # employee / part_timer / dummy
        count = role_info.get("count", 1)

        expanded_names = []
        for i in range(count):
            suffix = alpha[i] if i < len(alpha) else f"X{i}"
            expanded_name = f"{role_name}{suffix}"
            new_json["positions"][expanded_name] = rtype
            expanded_names.append(expanded_name)

        expanded_roles[role_name] = expanded_names

    #
    # (3) priority_assignments
    #
    new_json["priority_assignments"] = {}
    dummy_names = [f"N{i}" for i in range(1, 21)]

    capability_data = old_json.get("role_capability", {})
    for work_key, capability_info in capability_data.items():
        primary_roles = capability_info.get("primary", [])
        secondary_roles = capability_info.get("secondary", [])
        third_roles = capability_info.get("third", [])

        expanded_primary = []
        for r in primary_roles:
            expanded_primary.extend(expanded_roles.get(r, []))

        expanded_secondary = []
        for r in secondary_roles:
            expanded_secondary.extend(expanded_roles.get(r, []))

        # third は dummy固定
        expanded_third = dummy_names

        new_json["priority_assignments"][work_key] = {
            "primary": expanded_primary,
            "secondary": expanded_secondary,
            "third": expanded_third
        }

    #
    # (4) daily_requirements をそのままコピー
    #
    if "daily_requirements" in old_json:
        new_json["daily_requirements"] = {}
        for key, val in old_json["daily_requirements"].items():
            new_json["daily_requirements"][key] = {
                "normal_min": val.get("normal_min", 0),
                "normal_max": val.get("normal_max", 0),
                "friend_min": val.get("friend_min", 0),
                "friend_max": val.get("friend_max", 0)
            }

    #
    # (5) work_constraints をコピー
    #
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

    #
    # (6) dummy (N1〜N20) を positions に追加（もし未追加なら）
    #
    for dn in dummy_names:
        if dn not in new_json["positions"]:
            new_json["positions"][dn] = "dummy"

    #
    # (7) positions の並べ替え: employee → part_timer → dummy
    #
    position_items = list(new_json["positions"].items())
    type_order = {"employee": 0, "part_timer": 1, "dummy": 2}
    sorted_positions = sorted(position_items, key=lambda x: type_order.get(x[1], 99))
    new_json["positions"] = dict(sorted_positions)

    #
    # (8) 追加: カレンダー情報を付与
    #
    new_json["calendar"] = create_calendar(year)

    return new_json


def main():
    # (1) 旧JSONを読み込む
    with open(JSON_BEFORE, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    # (2) 変換
    new_data = transform_data(old_data)

    # (3) 新JSONを出力
    with open(JSON_AFTER, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print("✅ 変換が完了しました。")
    print(f"出力先: {JSON_AFTER}")


if __name__ == "__main__":
    main()
