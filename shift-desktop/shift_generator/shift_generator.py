import json
import pandas as pd
from ortools.sat.python import cp_model
import os
import sys


dir_name = sys.argv[1]  # 0番目はスクリプト名。1番目以降が引数。serevr.jsから受け取ったアウトプット用のディレクトリ名
print("受け取ったディレクトリ名:", dir_name)

current_path=os.getcwd()
#json_path = f"{current_path}/shift_generator/new.json"
json_path = f"./new.json"

month_map = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}

# 保存先のディレクトリを選択する
os.makedirs(os.path.join(current_path, f"${dir_name}"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "shifts"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "summary"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "work_days"), exist_ok=True)

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_variables(model, staff_list, days_in_month, work_types):
    x = {}
    for s in staff_list:
        x[s] = {}
        for d in range(days_in_month):
            x[s][d] = {}
            for w in work_types:
                x[s][d][w] = model.NewBoolVar(f"x_{s}_{d}_{w}")
    return x

def add_priority_constraints(model, x, config, staff_list, days_in_month, friend_days):
    """
    priority_assignmentsの各業務(w)に対し、
    primary/secondary/thirdの三段階で人数を満たす
    Minimize用に secondary_list, third_list を収集
    """
    friend_days = set(friend_days)
    daily_req   = config["daily_requirements"]
    priority_map= config["priority_assignments"]

    all_secondary_vars = []
    all_third_vars = []

    for w, pinfo in priority_map.items():
        # 3層に分ける
        primary_staff   = pinfo.get("primary", [])
        secondary_staff = pinfo.get("secondary", [])
        third_staff     = pinfo.get("third", [])

        for d in range(days_in_month):
            day_num = d + 1
            is_friend = (day_num in friend_days)
            if is_friend:
                min_req = daily_req[w]["friend_min"]
                max_req = daily_req[w]["friend_max"]
            else:
                min_req = daily_req[w]["normal_min"]
                max_req = daily_req[w]["normal_max"]
            sum_primary = sum(x[s][d][w] for s in primary_staff if s in staff_list)
            secondary_list = [x[s][d][w] for s in secondary_staff if s in staff_list]
            third_list_    = [x[s][d][w] for s in third_staff if s in staff_list]

            sum_secondary = sum(secondary_list)
            sum_third     = sum(third_list_)

            # constraint
            model.Add(sum_primary + sum_secondary + sum_third >= min_req)
            model.Add(sum_primary + sum_secondary + sum_third <= max_req)
            # second <= max_req - primary
            model.Add(sum_secondary <= max_req - sum_primary)
            # third <= max_req - (primary+secondary)
            model.Add(sum_third <= max_req - (sum_primary + sum_secondary))

            # 目的関数用に回収
            all_secondary_vars.extend(secondary_list)
            all_third_vars.extend(third_list_)

    return all_secondary_vars, all_third_vars

def add_daily_constraints_for_nonpriority(model, x, config, staff_list, days_in_month, friend_days):
    """
    priority_assignments に定義していない業務があれば、こちらで min/maxを処理
    (もし全業務をpriority_assignmentsに書くなら不要)
    """
    friend_days = set(friend_days)
    daily_req   = config["daily_requirements"]
    priority_map= config["priority_assignments"]
    work_types  = list(daily_req.keys())

    for w in work_types:
        if w in priority_map:
            continue  # priority扱いにスキップ
        # 非priority業務 => これまでの add_basic_daily_constraints と同様
        for d in range(days_in_month):
            day_num = d+1
            is_friend = (day_num in friend_days)
            if "normal_min" in daily_req[w] and "normal_max" in daily_req[w]:
                nm_min = daily_req[w]["normal_min"]
                nm_max = daily_req[w]["normal_max"]
                fm_min = daily_req[w].get("friend_min", nm_min)
                fm_max = daily_req[w].get("friend_max", nm_max)
                min_req = fm_min if is_friend else nm_min
                max_req = fm_max if is_friend else nm_max
            else:
                normal_val = daily_req[w].get("normal", 0)
                friend_val = daily_req[w].get("friend", normal_val)
                val = friend_val if is_friend else normal_val
                min_req = val
                max_req = val

            assign_vars = [x[s][d][w] for s in staff_list]  # すべて? or if s is in staff_list
            model.Add(sum(assign_vars) >= min_req)
            model.Add(sum(assign_vars) <= max_req)

def add_one_person_one_job_per_day(model, x, staff_list, days_in_month, work_types):
    for s in staff_list:
        for d in range(days_in_month):
            model.Add(sum(x[s][d][w] for w in work_types) <= 1)

def add_rest_constraints(model, x, config, staff_positions, staff_list, days_in_month, work_types):
    for s in staff_list:
        pos = staff_positions[s]
        wcon = config["work_constraints"][pos]
        required_days_off_7 = wcon["days_off_per_7days"]
        max_work_in_7 = 7 - required_days_off_7
        max_consec = wcon["max_consecutive_days"]
        min_month  = wcon["min_monthly_workdays"]

        # 7日中 (required_days_off_7)休み => max_work_in_7日勤務
        for start_day in range(days_in_month - 6):
            model.Add(
                sum(x[s][d][w] for d in range(start_day, start_day+7) for w in work_types)
                <= max_work_in_7
            )
        # 連続勤務
        if max_consec < days_in_month:
            for d in range(days_in_month - max_consec):
                model.Add(
                    sum(x[s][dd][w] for dd in range(d, d+max_consec+1) for w in work_types)
                    <= max_consec
                )
        # 月最低勤務
        if min_month > 0:
            model.Add(
                sum(x[s][d][w] for d in range(days_in_month) for w in work_types)
                >= min_month
            )

def add_fair_workday_constraints(model, x, staff_positions, staff_list, days_in_month, work_types):
    # 役職ごとのスタッフリスト作成（dummy除外）
    pos2staff = {}
    for s in staff_list:
        pos = staff_positions[s]
        if pos == "dummy":
            continue  # dummyは完全に除外
        pos2staff.setdefault(pos, []).append(s)

    for pos, staff_of_pos in pos2staff.items():
        if len(staff_of_pos) < 2:
            continue  # 一人しかいない役職はフェア制約不要

        workday_vars = []
        for s in staff_of_pos:
            var = model.NewIntVar(0, days_in_month, f"workdays_{s}")
            # その月の勤務日数カウント
            model.Add(var == sum(x[s][d][w] for d in range(days_in_month) for w in work_types))
            workday_vars.append(var)

        max_var = model.NewIntVar(0, days_in_month, f"{pos}_max_workdays")
        min_var = model.NewIntVar(0, days_in_month, f"{pos}_min_workdays")
        model.AddMaxEquality(max_var, workday_vars)
        model.AddMinEquality(min_var, workday_vars)

        # 差の許容量を役職ごとに設定
        if pos == "employee":
            diff = 1
        elif pos == "part_timer":
            diff = 3
        else:
            diff = 1  # 念のため（新しい役職が増えたとき用。調整可）

        model.Add(max_var - min_var <= diff)


def solve_with_or_tools(config, days_in_month, friend_days):
    # friend day
    friend_days = set(friend_days)
    
    # staff_list
    staff_positions = dict(config["positions"])
    staff_list = list(staff_positions.keys())
    work_types = list(config["daily_requirements"].keys())

    # モデル
    model = cp_model.CpModel()
    x = create_variables(model, staff_list, days_in_month, work_types)

    # ▼「priority_assignmentsに含まれないスタッフは業務wできない」制約
    priority_map = config["priority_assignments"]
    for w, pinfo in priority_map.items():
        union_set = set(pinfo.get("primary", [])) \
                  | set(pinfo.get("secondary", [])) \
                  | set(pinfo.get("third", []))
        for s in staff_list:
            if s not in union_set:
                for d in range(days_in_month):
                    model.Add(x[s][d][w] == 0)


    # primary+secondary+third constraints
    all_secondary_vars, all_third_vars = add_priority_constraints(model, x, config, staff_list, days_in_month, friend_days)

    # non-priority業務 (もしもpriority_assignments にない業務があるなら)
    add_daily_constraints_for_nonpriority(model, x, config, staff_list, days_in_month, friend_days)

    # 1日1人1業務
    add_one_person_one_job_per_day(model, x, staff_list, days_in_month, work_types)

    # rest constraints
    add_rest_constraints(model, x, config, staff_positions, staff_list, days_in_month, work_types)

    # フェア勤務日数制約（新たに追加）
    add_fair_workday_constraints(model, x, staff_positions, staff_list, days_in_month, work_types)


    # Minimize: sum(secondary) + 10000 * sum(third)
    # thirdの重みを大きくしてさらに優先度下げる
    COST_FACTOR_THIRD = 1000000
    model.Minimize(sum(all_secondary_vars) + COST_FACTOR_THIRD * sum(all_third_vars))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return status, None, staff_list, staff_positions, work_types

    # 解取り出し
    solution = {}
    for s in staff_list:
        solution[s] = []
        for d in range(days_in_month):
            assigned = ""
            for w in work_types:
                if solver.Value(x[s][d][w]) == 1:
                    assigned = w[0]
                    break
            solution[s].append(assigned)
    return status, solution, staff_list, staff_positions, work_types

def summarize_solution(solution, staff_positions, staff_list, days_in_month, work_types, month_key, config):
    year = config["year"]
    month_number = month_map[month_key]
    # 1〜3月は翌年、4〜12月はそのまま
    if month_number <= 3:
        actual_year = year + 1
    else:
        actual_year = year
    csv_suffix = f"{str(actual_year)[2:]}{month_number:02d}"

    staff_days = {}
    for s in staff_list:
        staff_days[s] = sum(1 for d in range(days_in_month) if solution[s][d] != "")

    day_records = []
    for d in range(days_in_month):
        working_staff = [s for s in staff_list if solution[s][d] != ""]
        total_work = len(working_staff)
        emp_count = sum(1 for s in working_staff if staff_positions[s] == "employee")
        pt_count  = sum(1 for s in working_staff if staff_positions[s] == "part_timer")
        dm_count  = sum(1 for s in working_staff if staff_positions[s] == "dummy")

        job_counts = {}
        for w in work_types:
            job_counts[w] = sum(solution[s][d] == w for s in working_staff)

        day_records.append({
            "day": d+1,
            "total_working": total_work,
            "employee_count": emp_count,
            "part_timer_count": pt_count,
            "dummy_count": dm_count,
            **{f"job_{w}": job_counts[w] for w in work_types}
        })

    df_staff_days = pd.DataFrame({
        "staff": staff_list,
        "total_workdays": [staff_days[s] for s in staff_list]
    }).set_index("staff")

    df_day_summary = pd.DataFrame(day_records).set_index("day")

    # シフト表
    df_shift = pd.DataFrame(index=staff_list, columns=range(1, days_in_month+1))
    for s in staff_list:
        for d in range(days_in_month):
            df_shift.at[s, d+1] = solution[s][d]

    print("\n=== 1) 従業員ごとの総勤務日数 ===")
    print(df_staff_days)
    print("\n=== 2) 日毎の出勤人数・業務内訳 ===")
    print(df_day_summary)
    print("\n=== 3) シフト表(従業員×日) ===")
    print(df_shift)
    # ▼ CSVファイル出力
    df_shift.to_csv(os.path.join(dir_name, "shifts", f"shift_result{csv_suffix}.csv"), encoding="utf-8-sig")
    df_staff_days.to_csv(os.path.join(dir_name, "summary", f"staff_workdays{csv_suffix}.csv"), encoding="utf-8-sig")
    df_day_summary.to_csv(os.path.join(dir_name, "work_days", f"day_summary{csv_suffix}.csv"), encoding="utf-8-sig")

    return df_staff_days, df_day_summary, df_shift

def main():
    # 4月(April)から翌年3月(March)までを回す例：
    months_to_process = [
        "April", "May", "June", "July", "August", "September",
        "October", "November", "December", "January", "February", "March"
    ]

    n=1
    for month_key in months_to_process:
        config = load_config(json_path)
        days_in_month = config["calendar"][month_key]["days_in_month"]
        friend_days   = config["calendar"][month_key]["friend_days"]
        print(f"=== {month_key} (days_in_month={days_in_month}) ===")

        # 月単位のシフトを生成
        status, solution, staff_list, staff_positions, work_types = solve_with_or_tools(
            config,
            days_in_month,
            friend_days
        )

        if solution is None:
            print("解が見つかりませんでした。")
            continue
        else:
            # ここでまとめ出力やCSV書き出し
            summarize_solution(
                solution,
                staff_positions,
                staff_list,
                days_in_month,
                work_types,
                month_key,
                config
            )
        
            # 解が見つかった。ダミーの割当をチェック
        # ダミーかどうかは positions で "dummy" と定義している想定
        dummy_used = False
        for s in staff_list:
            if staff_positions[s] == "dummy":
                # このスタッフが1日でも勤務していれば dummy_used=True
                for d in range(days_in_month):
                    if solution[s][d] != "":
                        dummy_used = True
                        break
            if dummy_used:
                break

        if dummy_used:
            print("=== ダミーが割り当てられました。以下のシフトに警告があります ===")
        else:
            print("=== シフトが見つかりました (ダミーなし) ===")

        # つづいて集計を表示
        #summarize_solution(solution, staff_positions, staff_list, days_in_month, work_types, config)

        # もし具体的にダミーが入った日付を列挙したいなら
        if dummy_used:
            shortage_list = []
            for d in range(days_in_month):
                for s in staff_list:
                    if staff_positions[s] == "dummy" and solution[s][d] != "":
                        shortage_list.append((d+1, s, solution[s][d]))
            if shortage_list:
                print("\n--- 警告: ダミー勤務箇所 ---")
                for (day_num, dummy_name, job) in shortage_list:
                    print(f"  Day {day_num}, Job '{job}' → {dummy_name}")

        n=n+1
    print("=== 全ての月の処理が完了しました ===")



if __name__ == "__main__":
    main()
