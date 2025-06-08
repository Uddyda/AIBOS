import json
from datetime import date

# ▼ 六曜の並び（先勝→友引→先負→仏滅→大安→赤口→再び先勝→... ）
ROKUYO_CYCLE = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]

# ▼ 基準となる日付と、その六曜（例：2001/1/1 は「仏滅」と決め打ち）
BASE_DATE = date(2001, 1, 1)
BASE_ROKUYO = "仏滅"
BASE_INDEX = ROKUYO_CYCLE.index(BASE_ROKUYO)

# ▼ 月番号 → 英語名 のマッピング
MONTH_NAMES = {
    1:  "January",
    2:  "February",
    3:  "March",
    4:  "April",
    5:  "May",
    6:  "June",
    7:  "July",
    8:  "August",
    9:  "September",
    10: "October",
    11: "November",
    12: "December"
}

def is_leap_year_simple(year: int) -> bool:
    """
    4の倍数の年をうるう年とする簡易版判定（例外規定は無視）。
    """
    return (year % 4 == 0)

def get_days_in_month(year: int, month: int) -> int:
    """
    指定年・月の「日数」を返す。
    4の倍数の年は2月を29日とする簡易版。
    """
    if month == 2:
        return 29 if is_leap_year_simple(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31

def get_rokuyo(current_date: date) -> str:
    """
    基準日との差分日数をもとに六曜を求める。
    """
    delta_days = (current_date - BASE_DATE).days
    # 基準日の六曜Indexに差分日数を加算し、6で割った余りをとる
    index = (BASE_INDEX + delta_days) % 6
    return ROKUYO_CYCLE[index]

def generate_rokuyo_calendar(target_year: int):
    """
    引数の「target_year」をもとに、target_year年4月1日～(target_year+1)年3月31日
    の期間における日付と六曜をJSON形式で出力する。
    """
    # 出力用データを格納する辞書
    # { "April": [ {"day": 1, "rokuyo": "仏滅"}, ... ], "May": [...], ... }
    calendar_data = {}

    # 4月(=4)～12月(=12) → target_year
    # 1月(=1)～3月(=3)   → target_year+1
    months_sequence = list(range(4, 13)) + list(range(1, 4))
    # 例：入力が2025なら → [4,5,6,7,8,9,10,11,12,1,2,3]
    #     4月～12月は2025年, 1月～3月は2026年

    for m in months_sequence:
        if m >= 4:
            y = target_year
        else:
            y = target_year + 1

        month_name = MONTH_NAMES[m]
        days_in_month = get_days_in_month(y, m)
        
        # 当該月の日＋六曜の情報をリスト化
        daily_list = []
        for day_num in range(1, days_in_month + 1):
            d = date(y, m, day_num)
            daily_list.append({
                "day": day_num,
                "rokuyo": get_rokuyo(d)
            })

        calendar_data[month_name] = daily_list

    # JSON文字列にシリアライズして返却（もしくはprintでも可）
    return json.dumps(calendar_data, ensure_ascii=False, indent=2)

# === 実行例 =============================================================
if __name__ == "__main__":
    target_year = 2025  # 例: 2025年度
    result_json = generate_rokuyo_calendar(target_year)
    print(result_json)
