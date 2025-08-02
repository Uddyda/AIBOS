import json
import os
from datetime import date
import calendar

try:
    from qreki import Kyureki  # type: ignore
except ModuleNotFoundError as e:
    raise SystemExit("\n[ERROR] QREKI ライブラリが見つかりません。\n"\
                     "以下を実行してから再試行してください:\n"\
                     "  pip install git+https://github.com/fgshun/qreki_py.git@v0.6.1\n") from e

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

def get_days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

def generate_rokuyo_calendar(target_year: int, verbose: bool = False) -> dict:
    """
    target_year年度 (4月1日〜翌3月31日) の六曜カレンダーを返す
    - 4月〜12月は target_year
    - 1月〜3月は target_year+1
    """
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
            rokuyo = kyureki.rokuyou
            if verbose:
                leap = getattr(kyureki, "is_leap", getattr(kyureki, "leap", False))
                print(f"{gdate.isoformat()} -> 旧暦 {kyureki.month}月{kyureki.day}日 (閏月={'Yes' if leap else 'No'}) → {rokuyo}")
            daily_list.append({"day": day, "rokuyo": rokuyo})
        calendar_data[month_name] = daily_list
    return {"year": target_year, "calendar": calendar_data}

if __name__ == "__main__":
    years = list(range(2001, 2101))  # 2001〜2100年
    all_data = []

    for y in years:
        print(f"年度: {y}")
        rokuyo_data = generate_rokuyo_calendar(y, verbose=False)
        all_data.append(rokuyo_data)

    out_file = "rokuyou.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(all_data, fp, ensure_ascii=False, indent=2)

    print("\n保存完了 →", out_file)
