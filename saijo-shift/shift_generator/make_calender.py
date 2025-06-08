import json
import os
from datetime import date

"""
rokuyo_calendar.py (改訂版)
-------------------------------------------------
日本の旧暦ロジック (QREKI) を用いて六曜を算出。
- https://github.com/fgshun/qreki_py
- pip install git+https://github.com/fgshun/qreki_py.git@v0.6.1#egg=qreki

【ポイント】
1. QREKI は天保暦ベースで日本の旧暦月長(29/30)を正確に扱う。
2. `Kyureki.from_date(gregorian_date).rokuyou` で六曜を直接取得。
3. (月+日)%6 の簡易計算を廃止し、実際の月長差異にも対応。
"""

# ----------------------------------------------------------------------------
# 依存ライブラリ
#   pip install git+https://github.com/fgshun/qreki_py.git@v0.6.1#egg=qreki
# ----------------------------------------------------------------------------
try:
    from qreki import Kyureki  # type: ignore
except ModuleNotFoundError as e:
    raise SystemExit("\n[ERROR] QREKI ライブラリが見つかりません。\n"\
                     "以下を実行してから再試行してください:\n"\
                     "  pip install git+https://github.com/fgshun/qreki_py.git@v0.6.1#egg=qreki\n") from e

# ----------------------------------------------------------------------------
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# 4の倍数をうるう年とみなす簡易ルール (西暦 1901-2099 範囲では十分)

def is_leap_year_simple(year: int) -> bool:
    return year % 4 == 0


def get_days_in_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if is_leap_year_simple(year) else 28
    return 30 if month in {4, 6, 9, 11} else 31

# ----------------------------------------------------------------------------
# カレンダー生成
# ----------------------------------------------------------------------------

def generate_rokuyo_calendar(target_year: int, verbose: bool = False) -> dict:
    """target_year年度 (4月1日〜翌3月31日) の六曜カレンダーを返す"""
    calendar_data = {}
    months_sequence = list(range(4, 13)) + list(range(1, 4))

    for month in months_sequence:
        year_for_month = target_year if month >= 4 else target_year + 1
        days_in_month = get_days_in_month(year_for_month, month)
        month_name = MONTH_NAMES[month]
        daily_list = []

        for day in range(1, days_in_month + 1):
            gdate = date(year_for_month, month, day)
            kyureki = Kyureki.from_date(gdate)
            rokuyo = kyureki.rokuyou  # 例: "友引"
            if verbose:
                leap = getattr(kyureki, "is_leap", getattr(kyureki, "leap", False))
                print(f"{gdate.isoformat()} -> 旧暦 {kyureki.month}月{kyureki.day}日 (閏月={'Yes' if leap else 'No'}) → {rokuyo}")
            daily_list.append({"day": day, "rokuyo": rokuyo})

        calendar_data[month_name] = daily_list

    return {"year": target_year, "calendar": calendar_data}

# ----------------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    current_path = os.getcwd()
    json_path = os.path.join(current_path, "../server", "output", "sample.json")

    with open(json_path, "r", encoding="utf-8") as fp:
        base_data = json.load(fp)

    target_year = int(base_data["year"])
    rokuyo_data = generate_rokuyo_calendar(target_year, verbose=True)

    out_file = f"rokuyou.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(rokuyo_data, fp, ensure_ascii=False, indent=2)

    print("\n保存完了 →", out_file)
