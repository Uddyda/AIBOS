import json
import calendar
import os

current_path = os.getcwd()
print(current_path)
# 旧JSONファイル (あなたの既存の入力用)
#JSON_BEFORE = "../server/output/define.json"
JSON_BEFORE = "../suidou.json"
# 新JSONファイル (変換後の出力先)
JSON_AFTER = "./new.json"
# 六曜情報を含むJSONファイル
ROKUYOU_JSON = "./rokuyou.json"

def create_calendar(year: int):
    """
    指定された 'year' の1～12月分の「days_in_month」と「友引の日(friend_days)」を
    ROKUYOU_JSON から取得して返す関数。

    【想定する rokuyou.json の構造】
    {
      "year": 2023,
      "calendar": {
        "April": [
          { "day": 1, "rokuyo": "赤口" },
          { "day": 2, "rokuyo": "先勝" },
          { "day": 3, "rokuyo": "友引" },
          ...
        ],
        "May": [...],
        ...
      }
    }

    ここでは month_names に沿って "January"～"December" のキーを見に行き、
    もし存在する場合のみ friend_days を抽出します。
    """
    # (1) rokuyou.json を読み込む
    with open(ROKUYOU_JSON, "r", encoding="utf-8") as f:
        rokuyou_data = json.load(f)

    # "calendar" キーに、月英名をキーとした六曜リストが入っている想定
    # 例: rokuyou_data["calendar"]["April"] = [ { "day": 1, "rokuyo": "赤口" }, ... ]
    input_calendar = rokuyou_data["calendar"]

    # 月英名と対応させるためのリスト
    month_names = [
        "April", "May", "June", "July", "August", "September",
        "October", "November", "December", "January", "February", "March", 
    ]

    # 結果を格納する辞書
    data = {}

    for m_name in month_names:
        # rokuyou.json の "calendar" 内に、この月名が無い場合はスキップ
        if m_name not in input_calendar:
            continue
        
        # 例: [ { "day": 1, "rokuyo": "赤口" }, { "day": 2, "rokuyo": "先勝" }, ... ]
        days_list = input_calendar[m_name]

        # days_in_month (月の日数) をリストの "day" の最大値から求める
        days_in_month = max(item["day"] for item in days_list)

        # rokuyo が "友引" の日だけ取り出す
        friend_days = [item["day"] for item in days_list if item["rokuyo"] == "友引"]

        # データを格納
        data[m_name] = {
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
    # (1) year を取得
    #
    # old_json に "year": 2025 のように指定がなければ、デフォルトを 2025 とする
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
            # たとえば i=0なら 'A', i=1なら 'B' ...
            suffix = alpha[i] if i < len(alpha) else f"X{i}"
            expanded_name = f"{role_name}{suffix}"
            new_json["positions"][expanded_name] = rtype
            expanded_names.append(expanded_name)

        # 例: "Manager" -> ["ManagerA", "ManagerB", ...]
        expanded_roles[role_name] = expanded_names

    #
    # (3) priority_assignments を生成
    #
    new_json["priority_assignments"] = {}
    dummy_names = [f"N{i}" for i in range(1, 21)]  # N1〜N20

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
    # (4) daily_requirements のコピー
    #
    if "daily_requirements" in old_json:
        new_json["daily_requirements"] = {}
        for key, val in old_json["daily_requirements"].items():
            # 例: { "normal_min": 2, "normal_max": 4, "friend_min": 1, "friend_max": 3 }
            new_json["daily_requirements"][key] = {
                "normal_min": val.get("normal_min", 0),
                "normal_max": val.get("normal_max", 0),
                "friend_min": val.get("friend_min", 0),
                "friend_max": val.get("friend_max", 0)
            }

    #
    # (5) work_constraints のコピー
    #
    if "work_constraints" in old_json:
        wc_old = old_json["work_constraints"]
        new_json["work_constraints"] = {}
        for wtype in ["employee", "part_timer", "dummy"]:
            if wtype in wc_old:
                # 例:
                # {
                #   "weekly_days_off": 2,
                #   "max_consecutive_days": 5,
                #   "min_monthly_workdays": 10
                # }
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
    # type_order.get(x[1], 99) により、employee=0, part_timer=1, dummy=2 と優先ソート
    sorted_positions = sorted(position_items, key=lambda x: type_order.get(x[1], 99))
    new_json["positions"] = dict(sorted_positions)

    #
    # (8) カレンダー情報を付与
    #     rokuyou.json から、指定した year の1～12月を走査し、友引の日を抽出する
    #
    new_json["calendar"] = create_calendar(year)

    return new_json


def main():
    """
    メイン処理:
    1) 旧JSON (sample.json) を読み込む
    2) transform_data() で新しい構造に変換
    3) new.json へ書き出す
    """
    # (1) 旧JSONを読み込む
    with open(JSON_BEFORE, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    # (2) 変換処理を実行
    new_data = transform_data(old_data)

    # (3) 新JSONを出力
    with open(JSON_AFTER, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print("✅ 変換が完了しました。")
    print(f"出力先: {JSON_AFTER}")


if __name__ == "__main__":
    main()
